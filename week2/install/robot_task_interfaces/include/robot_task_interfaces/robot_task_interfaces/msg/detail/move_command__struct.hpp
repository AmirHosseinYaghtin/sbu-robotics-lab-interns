// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from robot_task_interfaces:msg/MoveCommand.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_TASK_INTERFACES__MSG__DETAIL__MOVE_COMMAND__STRUCT_HPP_
#define ROBOT_TASK_INTERFACES__MSG__DETAIL__MOVE_COMMAND__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


// Include directives for member types
// Member 'waypoints'
#include "robot_task_interfaces/msg/detail/waypoint__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__robot_task_interfaces__msg__MoveCommand __attribute__((deprecated))
#else
# define DEPRECATED__robot_task_interfaces__msg__MoveCommand __declspec(deprecated)
#endif

namespace robot_task_interfaces
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct MoveCommand_
{
  using Type = MoveCommand_<ContainerAllocator>;

  explicit MoveCommand_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->action_label = "";
    }
  }

  explicit MoveCommand_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : action_label(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->action_label = "";
    }
  }

  // field types and members
  using _action_label_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _action_label_type action_label;
  using _waypoints_type =
    std::vector<robot_task_interfaces::msg::Waypoint_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<robot_task_interfaces::msg::Waypoint_<ContainerAllocator>>>;
  _waypoints_type waypoints;

  // setters for named parameter idiom
  Type & set__action_label(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->action_label = _arg;
    return *this;
  }
  Type & set__waypoints(
    const std::vector<robot_task_interfaces::msg::Waypoint_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<robot_task_interfaces::msg::Waypoint_<ContainerAllocator>>> & _arg)
  {
    this->waypoints = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    robot_task_interfaces::msg::MoveCommand_<ContainerAllocator> *;
  using ConstRawPtr =
    const robot_task_interfaces::msg::MoveCommand_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<robot_task_interfaces::msg::MoveCommand_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<robot_task_interfaces::msg::MoveCommand_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      robot_task_interfaces::msg::MoveCommand_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<robot_task_interfaces::msg::MoveCommand_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      robot_task_interfaces::msg::MoveCommand_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<robot_task_interfaces::msg::MoveCommand_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<robot_task_interfaces::msg::MoveCommand_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<robot_task_interfaces::msg::MoveCommand_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__robot_task_interfaces__msg__MoveCommand
    std::shared_ptr<robot_task_interfaces::msg::MoveCommand_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__robot_task_interfaces__msg__MoveCommand
    std::shared_ptr<robot_task_interfaces::msg::MoveCommand_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const MoveCommand_ & other) const
  {
    if (this->action_label != other.action_label) {
      return false;
    }
    if (this->waypoints != other.waypoints) {
      return false;
    }
    return true;
  }
  bool operator!=(const MoveCommand_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct MoveCommand_

// alias to use template instance with default allocator
using MoveCommand =
  robot_task_interfaces::msg::MoveCommand_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace robot_task_interfaces

#endif  // ROBOT_TASK_INTERFACES__MSG__DETAIL__MOVE_COMMAND__STRUCT_HPP_
