// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from robot_task_interfaces:msg/MoveCommand.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_TASK_INTERFACES__MSG__DETAIL__MOVE_COMMAND__TRAITS_HPP_
#define ROBOT_TASK_INTERFACES__MSG__DETAIL__MOVE_COMMAND__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "robot_task_interfaces/msg/detail/move_command__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'waypoints'
#include "robot_task_interfaces/msg/detail/waypoint__traits.hpp"

namespace robot_task_interfaces
{

namespace msg
{

inline void to_flow_style_yaml(
  const MoveCommand & msg,
  std::ostream & out)
{
  out << "{";
  // member: action_label
  {
    out << "action_label: ";
    rosidl_generator_traits::value_to_yaml(msg.action_label, out);
    out << ", ";
  }

  // member: waypoints
  {
    if (msg.waypoints.size() == 0) {
      out << "waypoints: []";
    } else {
      out << "waypoints: [";
      size_t pending_items = msg.waypoints.size();
      for (auto item : msg.waypoints) {
        to_flow_style_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const MoveCommand & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: action_label
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "action_label: ";
    rosidl_generator_traits::value_to_yaml(msg.action_label, out);
    out << "\n";
  }

  // member: waypoints
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.waypoints.size() == 0) {
      out << "waypoints: []\n";
    } else {
      out << "waypoints:\n";
      for (auto item : msg.waypoints) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "-\n";
        to_block_style_yaml(item, out, indentation + 2);
      }
    }
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const MoveCommand & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace msg

}  // namespace robot_task_interfaces

namespace rosidl_generator_traits
{

[[deprecated("use robot_task_interfaces::msg::to_block_style_yaml() instead")]]
inline void to_yaml(
  const robot_task_interfaces::msg::MoveCommand & msg,
  std::ostream & out, size_t indentation = 0)
{
  robot_task_interfaces::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use robot_task_interfaces::msg::to_yaml() instead")]]
inline std::string to_yaml(const robot_task_interfaces::msg::MoveCommand & msg)
{
  return robot_task_interfaces::msg::to_yaml(msg);
}

template<>
inline const char * data_type<robot_task_interfaces::msg::MoveCommand>()
{
  return "robot_task_interfaces::msg::MoveCommand";
}

template<>
inline const char * name<robot_task_interfaces::msg::MoveCommand>()
{
  return "robot_task_interfaces/msg/MoveCommand";
}

template<>
struct has_fixed_size<robot_task_interfaces::msg::MoveCommand>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<robot_task_interfaces::msg::MoveCommand>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<robot_task_interfaces::msg::MoveCommand>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // ROBOT_TASK_INTERFACES__MSG__DETAIL__MOVE_COMMAND__TRAITS_HPP_
