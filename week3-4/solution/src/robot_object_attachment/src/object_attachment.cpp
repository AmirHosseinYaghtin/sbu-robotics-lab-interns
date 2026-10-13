// Copyright 2026 SBU Robotics Lab
// SPDX-License-Identifier: Apache-2.0

#include <chrono>
#include <condition_variable>
#include <exception>
#include <functional>
#include <memory>
#include <mutex>
#include <stdexcept>
#include <string>
#include <utility>

#include <gazebo/common/Events.hh>
#include <gazebo/common/Plugin.hh>
#include <gazebo/physics/physics.hh>
#include <gazebo_ros/node.hpp>
#include <std_srvs/srv/trigger.hpp>

namespace robot_object_attachment
{
class ObjectAttachment : public gazebo::ModelPlugin
{
  using Trigger = std_srvs::srv::Trigger;

public:
  void Load(gazebo::physics::ModelPtr model, sdf::ElementPtr sdf) override
  {
    model_ = std::move(model);
    world_ = model_->GetWorld();
    link_ = model_->GetLink(sdf->Get<std::string>("object_link", "link").first);
    node_ = gazebo_ros::Node::Get(sdf);
    if (!link_) {
      RCLCPP_ERROR(node_->get_logger(), "Object attachment: object link does not exist");
      return;
    }
    parent_model_name_ = sdf->Get<std::string>("parent_model", "").first;
    parent_link_name_ = sdf->Get<std::string>("parent_link", "link5").first;
    grasp_offset_ = sdf->Get<ignition::math::Vector3d>(
      "grasp_offset", ignition::math::Vector3d(0.126, 0, 0)).first;
    max_distance_ = sdf->Get<double>("max_grasp_distance", 0.04).first;
    if (!(max_distance_ > 0)) {
      RCLCPP_ERROR(node_->get_logger(), "max_grasp_distance must be positive");
      return;
    }

    // Physics changes run on the update thread. A response is sent only after
    // the joint really exists / has been removed, never just after queueing it.
    update_ = gazebo::event::Events::ConnectWorldUpdateBegin(
      std::bind(&ObjectAttachment::Update, this));
    const auto prefix = "/" + model_->GetName();
    attach_service_ = node_->create_service<Trigger>(prefix + "/attach",
      [this](Trigger::Request::SharedPtr, Trigger::Response::SharedPtr response) {
        Request(true, response);
      });
    detach_service_ = node_->create_service<Trigger>(prefix + "/detach",
      [this](Trigger::Request::SharedPtr, Trigger::Response::SharedPtr response) {
        Request(false, response);
      });
    RCLCPP_INFO(node_->get_logger(), "Object attachment ready: %s/{attach,detach}",
      prefix.c_str());
  }

  void Reset() override
  {
    std::lock_guard<std::mutex> guard(mutex_);
    Detach();
    if (pending_) {
      pending_->message = "World reset while attachment request was pending";
      pending_->success = false;
      pending_.reset();
      condition_.notify_all();
    }
  }

private:
  void Request(bool attach, Trigger::Response::SharedPtr response)
  {
    std::unique_lock<std::mutex> lock(mutex_);
    if (pending_) {
      response->success = false;
      response->message = "Another attachment request is pending";
      return;
    }
    requested_attach_ = attach;
    pending_ = response;
    if (!condition_.wait_for(lock, std::chrono::seconds(2),
      [this]() {return !pending_;}))
    {
      // Cancel rather than letting a timed-out request attach on unpause.
      pending_.reset();
      response->success = false;
      response->message = "Gazebo is not updating; unpause the simulation and retry";
    }
  }

  void Update()
  {
    std::lock_guard<std::mutex> guard(mutex_);
    if (!pending_) {
      return;
    }
    try {
      if (requested_attach_) {
        Attach();
        pending_->message = "Object attached to " + parent_->GetScopedName();
      } else {
        Detach();
        pending_->message = "Object released; collisions restored";
      }
      pending_->success = true;
    } catch (const std::exception & error) {
      pending_->success = false;
      pending_->message = error.what();
    }
    pending_.reset();
    condition_.notify_all();
  }

  gazebo::physics::LinkPtr FindParent()
  {
    gazebo::physics::LinkPtr result;
    for (const auto & candidate : world_->Models()) {
      if (candidate == model_ ||
        (!parent_model_name_.empty() && candidate->GetName() != parent_model_name_))
      {
        continue;
      }
      auto link = candidate->GetLink(parent_link_name_);
      if (link) {
        if (result) {
          throw std::runtime_error("Multiple robots have the gripper link; set parent_model");
        }
        result = link;
      }
    }
    if (!result) {
      throw std::runtime_error("Cannot find robot gripper link: " + parent_link_name_);
    }
    return result;
  }

  void Attach()
  {
    if (joint_) {
      return;  // Idempotent: never create two constraints for one cube.
    }
    auto parent = FindParent();
    const auto tip = parent->WorldPose().Pos() +
      parent->WorldPose().Rot().RotateVector(grasp_offset_);
    const double distance = (link_->WorldPose().Pos() - tip).Length();
    if (!(distance <= max_distance_)) {
      throw std::runtime_error("Object is not between the fingers (tip distance " +
              std::to_string(distance) + " m); check grasp pose before attaching");
    }
    auto joint = world_->Physics()->CreateJoint("fixed", model_);
    if (!joint) {
      throw std::runtime_error("Physics engine cannot create a fixed grasp joint");
    }
    try {
      joint->SetName(model_->GetName() + "_grasp_joint");
      // Preserve the measured relative pose: do not teleport the cube to link5.
      joint->Load(parent, link_, ignition::math::Pose3d::Zero);
      joint->Init();
      // The fixed joint now holds the cube. Finger contacts must not fight it
      // while the gripper closes. Both category and collide masks are disabled.
      link_->SetCollideMode("none");
      link_->SetLinearVel(ignition::math::Vector3d::Zero);
      link_->SetAngularVel(ignition::math::Vector3d::Zero);
    } catch (...) {
      joint->Detach();
      joint->Fini();
      link_->SetCollideMode("all");
      throw;
    }
    parent_ = parent;
    joint_ = joint;
  }

  void Detach()
  {
    if (!joint_) {
      return;
    }
    joint_->Detach();
    joint_->Fini();
    joint_.reset();
    parent_.reset();
    // Called after OPEN_GRIPPER. Zero residual velocity before restoring
    // contacts so the released cube settles onto the place stand.
    link_->SetLinearVel(ignition::math::Vector3d::Zero);
    link_->SetAngularVel(ignition::math::Vector3d::Zero);
    link_->SetCollideMode("all");
  }

  gazebo::physics::ModelPtr model_;
  gazebo::physics::WorldPtr world_;
  gazebo::physics::LinkPtr link_;
  gazebo::physics::LinkPtr parent_;
  gazebo::physics::JointPtr joint_;
  gazebo_ros::Node::SharedPtr node_;
  gazebo::event::ConnectionPtr update_;
  rclcpp::Service<Trigger>::SharedPtr attach_service_;
  rclcpp::Service<Trigger>::SharedPtr detach_service_;
  std::string parent_model_name_;
  std::string parent_link_name_;
  ignition::math::Vector3d grasp_offset_;
  double max_distance_ = 0.04;
  std::mutex mutex_;
  std::condition_variable condition_;
  Trigger::Response::SharedPtr pending_;
  bool requested_attach_ = false;
};

GZ_REGISTER_MODEL_PLUGIN(ObjectAttachment)
}  // namespace robot_object_attachment
