// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from robot_task_interfaces:srv/GetRobotStatus.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_TASK_INTERFACES__SRV__DETAIL__GET_ROBOT_STATUS__STRUCT_HPP_
#define ROBOT_TASK_INTERFACES__SRV__DETAIL__GET_ROBOT_STATUS__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__robot_task_interfaces__srv__GetRobotStatus_Request __attribute__((deprecated))
#else
# define DEPRECATED__robot_task_interfaces__srv__GetRobotStatus_Request __declspec(deprecated)
#endif

namespace robot_task_interfaces
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct GetRobotStatus_Request_
{
  using Type = GetRobotStatus_Request_<ContainerAllocator>;

  explicit GetRobotStatus_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->structure_needs_at_least_one_member = 0;
    }
  }

  explicit GetRobotStatus_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->structure_needs_at_least_one_member = 0;
    }
  }

  // field types and members
  using _structure_needs_at_least_one_member_type =
    uint8_t;
  _structure_needs_at_least_one_member_type structure_needs_at_least_one_member;


  // constant declarations

  // pointer types
  using RawPtr =
    robot_task_interfaces::srv::GetRobotStatus_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const robot_task_interfaces::srv::GetRobotStatus_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<robot_task_interfaces::srv::GetRobotStatus_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<robot_task_interfaces::srv::GetRobotStatus_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      robot_task_interfaces::srv::GetRobotStatus_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<robot_task_interfaces::srv::GetRobotStatus_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      robot_task_interfaces::srv::GetRobotStatus_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<robot_task_interfaces::srv::GetRobotStatus_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<robot_task_interfaces::srv::GetRobotStatus_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<robot_task_interfaces::srv::GetRobotStatus_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__robot_task_interfaces__srv__GetRobotStatus_Request
    std::shared_ptr<robot_task_interfaces::srv::GetRobotStatus_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__robot_task_interfaces__srv__GetRobotStatus_Request
    std::shared_ptr<robot_task_interfaces::srv::GetRobotStatus_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const GetRobotStatus_Request_ & other) const
  {
    if (this->structure_needs_at_least_one_member != other.structure_needs_at_least_one_member) {
      return false;
    }
    return true;
  }
  bool operator!=(const GetRobotStatus_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct GetRobotStatus_Request_

// alias to use template instance with default allocator
using GetRobotStatus_Request =
  robot_task_interfaces::srv::GetRobotStatus_Request_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace robot_task_interfaces


#ifndef _WIN32
# define DEPRECATED__robot_task_interfaces__srv__GetRobotStatus_Response __attribute__((deprecated))
#else
# define DEPRECATED__robot_task_interfaces__srv__GetRobotStatus_Response __declspec(deprecated)
#endif

namespace robot_task_interfaces
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct GetRobotStatus_Response_
{
  using Type = GetRobotStatus_Response_<ContainerAllocator>;

  explicit GetRobotStatus_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->status = "";
      this->current_action = "";
      this->elapsed_time = 0.0;
    }
  }

  explicit GetRobotStatus_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : status(_alloc),
    current_action(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->status = "";
      this->current_action = "";
      this->elapsed_time = 0.0;
    }
  }

  // field types and members
  using _status_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _status_type status;
  using _current_action_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _current_action_type current_action;
  using _elapsed_time_type =
    double;
  _elapsed_time_type elapsed_time;

  // setters for named parameter idiom
  Type & set__status(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->status = _arg;
    return *this;
  }
  Type & set__current_action(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->current_action = _arg;
    return *this;
  }
  Type & set__elapsed_time(
    const double & _arg)
  {
    this->elapsed_time = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    robot_task_interfaces::srv::GetRobotStatus_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const robot_task_interfaces::srv::GetRobotStatus_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<robot_task_interfaces::srv::GetRobotStatus_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<robot_task_interfaces::srv::GetRobotStatus_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      robot_task_interfaces::srv::GetRobotStatus_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<robot_task_interfaces::srv::GetRobotStatus_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      robot_task_interfaces::srv::GetRobotStatus_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<robot_task_interfaces::srv::GetRobotStatus_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<robot_task_interfaces::srv::GetRobotStatus_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<robot_task_interfaces::srv::GetRobotStatus_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__robot_task_interfaces__srv__GetRobotStatus_Response
    std::shared_ptr<robot_task_interfaces::srv::GetRobotStatus_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__robot_task_interfaces__srv__GetRobotStatus_Response
    std::shared_ptr<robot_task_interfaces::srv::GetRobotStatus_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const GetRobotStatus_Response_ & other) const
  {
    if (this->status != other.status) {
      return false;
    }
    if (this->current_action != other.current_action) {
      return false;
    }
    if (this->elapsed_time != other.elapsed_time) {
      return false;
    }
    return true;
  }
  bool operator!=(const GetRobotStatus_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct GetRobotStatus_Response_

// alias to use template instance with default allocator
using GetRobotStatus_Response =
  robot_task_interfaces::srv::GetRobotStatus_Response_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace robot_task_interfaces

namespace robot_task_interfaces
{

namespace srv
{

struct GetRobotStatus
{
  using Request = robot_task_interfaces::srv::GetRobotStatus_Request;
  using Response = robot_task_interfaces::srv::GetRobotStatus_Response;
};

}  // namespace srv

}  // namespace robot_task_interfaces

#endif  // ROBOT_TASK_INTERFACES__SRV__DETAIL__GET_ROBOT_STATUS__STRUCT_HPP_
