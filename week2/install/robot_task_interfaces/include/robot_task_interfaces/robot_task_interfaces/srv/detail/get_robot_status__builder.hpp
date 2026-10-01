// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from robot_task_interfaces:srv/GetRobotStatus.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_TASK_INTERFACES__SRV__DETAIL__GET_ROBOT_STATUS__BUILDER_HPP_
#define ROBOT_TASK_INTERFACES__SRV__DETAIL__GET_ROBOT_STATUS__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "robot_task_interfaces/srv/detail/get_robot_status__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace robot_task_interfaces
{

namespace srv
{


}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::robot_task_interfaces::srv::GetRobotStatus_Request>()
{
  return ::robot_task_interfaces::srv::GetRobotStatus_Request(rosidl_runtime_cpp::MessageInitialization::ZERO);
}

}  // namespace robot_task_interfaces


namespace robot_task_interfaces
{

namespace srv
{

namespace builder
{

class Init_GetRobotStatus_Response_elapsed_time
{
public:
  explicit Init_GetRobotStatus_Response_elapsed_time(::robot_task_interfaces::srv::GetRobotStatus_Response & msg)
  : msg_(msg)
  {}
  ::robot_task_interfaces::srv::GetRobotStatus_Response elapsed_time(::robot_task_interfaces::srv::GetRobotStatus_Response::_elapsed_time_type arg)
  {
    msg_.elapsed_time = std::move(arg);
    return std::move(msg_);
  }

private:
  ::robot_task_interfaces::srv::GetRobotStatus_Response msg_;
};

class Init_GetRobotStatus_Response_current_action
{
public:
  explicit Init_GetRobotStatus_Response_current_action(::robot_task_interfaces::srv::GetRobotStatus_Response & msg)
  : msg_(msg)
  {}
  Init_GetRobotStatus_Response_elapsed_time current_action(::robot_task_interfaces::srv::GetRobotStatus_Response::_current_action_type arg)
  {
    msg_.current_action = std::move(arg);
    return Init_GetRobotStatus_Response_elapsed_time(msg_);
  }

private:
  ::robot_task_interfaces::srv::GetRobotStatus_Response msg_;
};

class Init_GetRobotStatus_Response_status
{
public:
  Init_GetRobotStatus_Response_status()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_GetRobotStatus_Response_current_action status(::robot_task_interfaces::srv::GetRobotStatus_Response::_status_type arg)
  {
    msg_.status = std::move(arg);
    return Init_GetRobotStatus_Response_current_action(msg_);
  }

private:
  ::robot_task_interfaces::srv::GetRobotStatus_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::robot_task_interfaces::srv::GetRobotStatus_Response>()
{
  return robot_task_interfaces::srv::builder::Init_GetRobotStatus_Response_status();
}

}  // namespace robot_task_interfaces

#endif  // ROBOT_TASK_INTERFACES__SRV__DETAIL__GET_ROBOT_STATUS__BUILDER_HPP_
