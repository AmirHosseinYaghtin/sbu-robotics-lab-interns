// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from robot_task_interfaces:msg/MoveCommand.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "robot_task_interfaces/msg/detail/move_command__rosidl_typesupport_introspection_c.h"
#include "robot_task_interfaces/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "robot_task_interfaces/msg/detail/move_command__functions.h"
#include "robot_task_interfaces/msg/detail/move_command__struct.h"


// Include directives for member types
// Member `action_label`
#include "rosidl_runtime_c/string_functions.h"
// Member `waypoints`
#include "robot_task_interfaces/msg/waypoint.h"
// Member `waypoints`
#include "robot_task_interfaces/msg/detail/waypoint__rosidl_typesupport_introspection_c.h"

#ifdef __cplusplus
extern "C"
{
#endif

void robot_task_interfaces__msg__MoveCommand__rosidl_typesupport_introspection_c__MoveCommand_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  robot_task_interfaces__msg__MoveCommand__init(message_memory);
}

void robot_task_interfaces__msg__MoveCommand__rosidl_typesupport_introspection_c__MoveCommand_fini_function(void * message_memory)
{
  robot_task_interfaces__msg__MoveCommand__fini(message_memory);
}

size_t robot_task_interfaces__msg__MoveCommand__rosidl_typesupport_introspection_c__size_function__MoveCommand__waypoints(
  const void * untyped_member)
{
  const robot_task_interfaces__msg__Waypoint__Sequence * member =
    (const robot_task_interfaces__msg__Waypoint__Sequence *)(untyped_member);
  return member->size;
}

const void * robot_task_interfaces__msg__MoveCommand__rosidl_typesupport_introspection_c__get_const_function__MoveCommand__waypoints(
  const void * untyped_member, size_t index)
{
  const robot_task_interfaces__msg__Waypoint__Sequence * member =
    (const robot_task_interfaces__msg__Waypoint__Sequence *)(untyped_member);
  return &member->data[index];
}

void * robot_task_interfaces__msg__MoveCommand__rosidl_typesupport_introspection_c__get_function__MoveCommand__waypoints(
  void * untyped_member, size_t index)
{
  robot_task_interfaces__msg__Waypoint__Sequence * member =
    (robot_task_interfaces__msg__Waypoint__Sequence *)(untyped_member);
  return &member->data[index];
}

void robot_task_interfaces__msg__MoveCommand__rosidl_typesupport_introspection_c__fetch_function__MoveCommand__waypoints(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const robot_task_interfaces__msg__Waypoint * item =
    ((const robot_task_interfaces__msg__Waypoint *)
    robot_task_interfaces__msg__MoveCommand__rosidl_typesupport_introspection_c__get_const_function__MoveCommand__waypoints(untyped_member, index));
  robot_task_interfaces__msg__Waypoint * value =
    (robot_task_interfaces__msg__Waypoint *)(untyped_value);
  *value = *item;
}

void robot_task_interfaces__msg__MoveCommand__rosidl_typesupport_introspection_c__assign_function__MoveCommand__waypoints(
  void * untyped_member, size_t index, const void * untyped_value)
{
  robot_task_interfaces__msg__Waypoint * item =
    ((robot_task_interfaces__msg__Waypoint *)
    robot_task_interfaces__msg__MoveCommand__rosidl_typesupport_introspection_c__get_function__MoveCommand__waypoints(untyped_member, index));
  const robot_task_interfaces__msg__Waypoint * value =
    (const robot_task_interfaces__msg__Waypoint *)(untyped_value);
  *item = *value;
}

bool robot_task_interfaces__msg__MoveCommand__rosidl_typesupport_introspection_c__resize_function__MoveCommand__waypoints(
  void * untyped_member, size_t size)
{
  robot_task_interfaces__msg__Waypoint__Sequence * member =
    (robot_task_interfaces__msg__Waypoint__Sequence *)(untyped_member);
  robot_task_interfaces__msg__Waypoint__Sequence__fini(member);
  return robot_task_interfaces__msg__Waypoint__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember robot_task_interfaces__msg__MoveCommand__rosidl_typesupport_introspection_c__MoveCommand_message_member_array[2] = {
  {
    "action_label",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(robot_task_interfaces__msg__MoveCommand, action_label),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "waypoints",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(robot_task_interfaces__msg__MoveCommand, waypoints),  // bytes offset in struct
    NULL,  // default value
    robot_task_interfaces__msg__MoveCommand__rosidl_typesupport_introspection_c__size_function__MoveCommand__waypoints,  // size() function pointer
    robot_task_interfaces__msg__MoveCommand__rosidl_typesupport_introspection_c__get_const_function__MoveCommand__waypoints,  // get_const(index) function pointer
    robot_task_interfaces__msg__MoveCommand__rosidl_typesupport_introspection_c__get_function__MoveCommand__waypoints,  // get(index) function pointer
    robot_task_interfaces__msg__MoveCommand__rosidl_typesupport_introspection_c__fetch_function__MoveCommand__waypoints,  // fetch(index, &value) function pointer
    robot_task_interfaces__msg__MoveCommand__rosidl_typesupport_introspection_c__assign_function__MoveCommand__waypoints,  // assign(index, value) function pointer
    robot_task_interfaces__msg__MoveCommand__rosidl_typesupport_introspection_c__resize_function__MoveCommand__waypoints  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers robot_task_interfaces__msg__MoveCommand__rosidl_typesupport_introspection_c__MoveCommand_message_members = {
  "robot_task_interfaces__msg",  // message namespace
  "MoveCommand",  // message name
  2,  // number of fields
  sizeof(robot_task_interfaces__msg__MoveCommand),
  robot_task_interfaces__msg__MoveCommand__rosidl_typesupport_introspection_c__MoveCommand_message_member_array,  // message members
  robot_task_interfaces__msg__MoveCommand__rosidl_typesupport_introspection_c__MoveCommand_init_function,  // function to initialize message memory (memory has to be allocated)
  robot_task_interfaces__msg__MoveCommand__rosidl_typesupport_introspection_c__MoveCommand_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t robot_task_interfaces__msg__MoveCommand__rosidl_typesupport_introspection_c__MoveCommand_message_type_support_handle = {
  0,
  &robot_task_interfaces__msg__MoveCommand__rosidl_typesupport_introspection_c__MoveCommand_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_robot_task_interfaces
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, robot_task_interfaces, msg, MoveCommand)() {
  robot_task_interfaces__msg__MoveCommand__rosidl_typesupport_introspection_c__MoveCommand_message_member_array[1].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, robot_task_interfaces, msg, Waypoint)();
  if (!robot_task_interfaces__msg__MoveCommand__rosidl_typesupport_introspection_c__MoveCommand_message_type_support_handle.typesupport_identifier) {
    robot_task_interfaces__msg__MoveCommand__rosidl_typesupport_introspection_c__MoveCommand_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &robot_task_interfaces__msg__MoveCommand__rosidl_typesupport_introspection_c__MoveCommand_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
