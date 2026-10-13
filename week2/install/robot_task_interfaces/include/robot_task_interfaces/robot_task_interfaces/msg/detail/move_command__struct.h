// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from robot_task_interfaces:msg/MoveCommand.idl
// generated code does not contain a copyright notice

#ifndef ROBOT_TASK_INTERFACES__MSG__DETAIL__MOVE_COMMAND__STRUCT_H_
#define ROBOT_TASK_INTERFACES__MSG__DETAIL__MOVE_COMMAND__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'action_label'
#include "rosidl_runtime_c/string.h"
// Member 'waypoints'
#include "robot_task_interfaces/msg/detail/waypoint__struct.h"

/// Struct defined in msg/MoveCommand in the package robot_task_interfaces.
typedef struct robot_task_interfaces__msg__MoveCommand
{
  rosidl_runtime_c__String action_label;
  robot_task_interfaces__msg__Waypoint__Sequence waypoints;
} robot_task_interfaces__msg__MoveCommand;

// Struct for a sequence of robot_task_interfaces__msg__MoveCommand.
typedef struct robot_task_interfaces__msg__MoveCommand__Sequence
{
  robot_task_interfaces__msg__MoveCommand * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} robot_task_interfaces__msg__MoveCommand__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // ROBOT_TASK_INTERFACES__MSG__DETAIL__MOVE_COMMAND__STRUCT_H_
