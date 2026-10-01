// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from robot_task_interfaces:srv/GetRobotStatus.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_TASK_INTERFACES__SRV__DETAIL__GET_ROBOT_STATUS__TRAITS_HPP_
#define ROBOT_TASK_INTERFACES__SRV__DETAIL__GET_ROBOT_STATUS__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "robot_task_interfaces/srv/detail/get_robot_status__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace robot_task_interfaces
{

namespace srv
{

inline void to_flow_style_yaml(
  const GetRobotStatus_Request & msg,
  std::ostream & out)
{
  (void)msg;
  out << "null";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const GetRobotStatus_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  (void)msg;
  (void)indentation;
  out << "null\n";
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const GetRobotStatus_Request & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace srv

}  // namespace robot_task_interfaces

namespace rosidl_generator_traits
{

[[deprecated("use robot_task_interfaces::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const robot_task_interfaces::srv::GetRobotStatus_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  robot_task_interfaces::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use robot_task_interfaces::srv::to_yaml() instead")]]
inline std::string to_yaml(const robot_task_interfaces::srv::GetRobotStatus_Request & msg)
{
  return robot_task_interfaces::srv::to_yaml(msg);
}

template<>
inline const char * data_type<robot_task_interfaces::srv::GetRobotStatus_Request>()
{
  return "robot_task_interfaces::srv::GetRobotStatus_Request";
}

template<>
inline const char * name<robot_task_interfaces::srv::GetRobotStatus_Request>()
{
  return "robot_task_interfaces/srv/GetRobotStatus_Request";
}

template<>
struct has_fixed_size<robot_task_interfaces::srv::GetRobotStatus_Request>
  : std::integral_constant<bool, true> {};

template<>
struct has_bounded_size<robot_task_interfaces::srv::GetRobotStatus_Request>
  : std::integral_constant<bool, true> {};

template<>
struct is_message<robot_task_interfaces::srv::GetRobotStatus_Request>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace robot_task_interfaces
{

namespace srv
{

inline void to_flow_style_yaml(
  const GetRobotStatus_Response & msg,
  std::ostream & out)
{
  out << "{";
  // member: status
  {
    out << "status: ";
    rosidl_generator_traits::value_to_yaml(msg.status, out);
    out << ", ";
  }

  // member: current_action
  {
    out << "current_action: ";
    rosidl_generator_traits::value_to_yaml(msg.current_action, out);
    out << ", ";
  }

  // member: elapsed_time
  {
    out << "elapsed_time: ";
    rosidl_generator_traits::value_to_yaml(msg.elapsed_time, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const GetRobotStatus_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: status
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "status: ";
    rosidl_generator_traits::value_to_yaml(msg.status, out);
    out << "\n";
  }

  // member: current_action
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "current_action: ";
    rosidl_generator_traits::value_to_yaml(msg.current_action, out);
    out << "\n";
  }

  // member: elapsed_time
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "elapsed_time: ";
    rosidl_generator_traits::value_to_yaml(msg.elapsed_time, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const GetRobotStatus_Response & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace srv

}  // namespace robot_task_interfaces

namespace rosidl_generator_traits
{

[[deprecated("use robot_task_interfaces::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const robot_task_interfaces::srv::GetRobotStatus_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  robot_task_interfaces::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use robot_task_interfaces::srv::to_yaml() instead")]]
inline std::string to_yaml(const robot_task_interfaces::srv::GetRobotStatus_Response & msg)
{
  return robot_task_interfaces::srv::to_yaml(msg);
}

template<>
inline const char * data_type<robot_task_interfaces::srv::GetRobotStatus_Response>()
{
  return "robot_task_interfaces::srv::GetRobotStatus_Response";
}

template<>
inline const char * name<robot_task_interfaces::srv::GetRobotStatus_Response>()
{
  return "robot_task_interfaces/srv/GetRobotStatus_Response";
}

template<>
struct has_fixed_size<robot_task_interfaces::srv::GetRobotStatus_Response>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<robot_task_interfaces::srv::GetRobotStatus_Response>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<robot_task_interfaces::srv::GetRobotStatus_Response>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<robot_task_interfaces::srv::GetRobotStatus>()
{
  return "robot_task_interfaces::srv::GetRobotStatus";
}

template<>
inline const char * name<robot_task_interfaces::srv::GetRobotStatus>()
{
  return "robot_task_interfaces/srv/GetRobotStatus";
}

template<>
struct has_fixed_size<robot_task_interfaces::srv::GetRobotStatus>
  : std::integral_constant<
    bool,
    has_fixed_size<robot_task_interfaces::srv::GetRobotStatus_Request>::value &&
    has_fixed_size<robot_task_interfaces::srv::GetRobotStatus_Response>::value
  >
{
};

template<>
struct has_bounded_size<robot_task_interfaces::srv::GetRobotStatus>
  : std::integral_constant<
    bool,
    has_bounded_size<robot_task_interfaces::srv::GetRobotStatus_Request>::value &&
    has_bounded_size<robot_task_interfaces::srv::GetRobotStatus_Response>::value
  >
{
};

template<>
struct is_service<robot_task_interfaces::srv::GetRobotStatus>
  : std::true_type
{
};

template<>
struct is_service_request<robot_task_interfaces::srv::GetRobotStatus_Request>
  : std::true_type
{
};

template<>
struct is_service_response<robot_task_interfaces::srv::GetRobotStatus_Response>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits

#endif  // ROBOT_TASK_INTERFACES__SRV__DETAIL__GET_ROBOT_STATUS__TRAITS_HPP_
