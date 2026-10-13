// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from robot_task_interfaces:msg/Waypoint.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_TASK_INTERFACES__MSG__DETAIL__WAYPOINT__BUILDER_HPP_
#define ROBOT_TASK_INTERFACES__MSG__DETAIL__WAYPOINT__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "robot_task_interfaces/msg/detail/waypoint__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace robot_task_interfaces
{

namespace msg
{

namespace builder
{

class Init_Waypoint_theta
{
public:
  explicit Init_Waypoint_theta(::robot_task_interfaces::msg::Waypoint & msg)
  : msg_(msg)
  {}
  ::robot_task_interfaces::msg::Waypoint theta(::robot_task_interfaces::msg::Waypoint::_theta_type arg)
  {
    msg_.theta = std::move(arg);
    return std::move(msg_);
  }

private:
  ::robot_task_interfaces::msg::Waypoint msg_;
};

class Init_Waypoint_y
{
public:
  explicit Init_Waypoint_y(::robot_task_interfaces::msg::Waypoint & msg)
  : msg_(msg)
  {}
  Init_Waypoint_theta y(::robot_task_interfaces::msg::Waypoint::_y_type arg)
  {
    msg_.y = std::move(arg);
    return Init_Waypoint_theta(msg_);
  }

private:
  ::robot_task_interfaces::msg::Waypoint msg_;
};

class Init_Waypoint_x
{
public:
  Init_Waypoint_x()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_Waypoint_y x(::robot_task_interfaces::msg::Waypoint::_x_type arg)
  {
    msg_.x = std::move(arg);
    return Init_Waypoint_y(msg_);
  }

private:
  ::robot_task_interfaces::msg::Waypoint msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::robot_task_interfaces::msg::Waypoint>()
{
  return robot_task_interfaces::msg::builder::Init_Waypoint_x();
}

}  // namespace robot_task_interfaces

#endif  // ROBOT_TASK_INTERFACES__MSG__DETAIL__WAYPOINT__BUILDER_HPP_
