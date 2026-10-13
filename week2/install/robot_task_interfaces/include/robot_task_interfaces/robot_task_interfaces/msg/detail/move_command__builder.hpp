// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from robot_task_interfaces:msg/MoveCommand.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_TASK_INTERFACES__MSG__DETAIL__MOVE_COMMAND__BUILDER_HPP_
#define ROBOT_TASK_INTERFACES__MSG__DETAIL__MOVE_COMMAND__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "robot_task_interfaces/msg/detail/move_command__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace robot_task_interfaces
{

namespace msg
{

namespace builder
{

class Init_MoveCommand_waypoints
{
public:
  explicit Init_MoveCommand_waypoints(::robot_task_interfaces::msg::MoveCommand & msg)
  : msg_(msg)
  {}
  ::robot_task_interfaces::msg::MoveCommand waypoints(::robot_task_interfaces::msg::MoveCommand::_waypoints_type arg)
  {
    msg_.waypoints = std::move(arg);
    return std::move(msg_);
  }

private:
  ::robot_task_interfaces::msg::MoveCommand msg_;
};

class Init_MoveCommand_action_label
{
public:
  Init_MoveCommand_action_label()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_MoveCommand_waypoints action_label(::robot_task_interfaces::msg::MoveCommand::_action_label_type arg)
  {
    msg_.action_label = std::move(arg);
    return Init_MoveCommand_waypoints(msg_);
  }

private:
  ::robot_task_interfaces::msg::MoveCommand msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::robot_task_interfaces::msg::MoveCommand>()
{
  return robot_task_interfaces::msg::builder::Init_MoveCommand_action_label();
}

}  // namespace robot_task_interfaces

#endif  // ROBOT_TASK_INTERFACES__MSG__DETAIL__MOVE_COMMAND__BUILDER_HPP_
