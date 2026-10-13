// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from robot_task_interfaces:msg/MoveCommand.idl
// generated code does not contain a copyright notice
#include "robot_task_interfaces/msg/detail/move_command__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `action_label`
#include "rosidl_runtime_c/string_functions.h"
// Member `waypoints`
#include "robot_task_interfaces/msg/detail/waypoint__functions.h"

bool
robot_task_interfaces__msg__MoveCommand__init(robot_task_interfaces__msg__MoveCommand * msg)
{
  if (!msg) {
    return false;
  }
  // action_label
  if (!rosidl_runtime_c__String__init(&msg->action_label)) {
    robot_task_interfaces__msg__MoveCommand__fini(msg);
    return false;
  }
  // waypoints
  if (!robot_task_interfaces__msg__Waypoint__Sequence__init(&msg->waypoints, 0)) {
    robot_task_interfaces__msg__MoveCommand__fini(msg);
    return false;
  }
  return true;
}

void
robot_task_interfaces__msg__MoveCommand__fini(robot_task_interfaces__msg__MoveCommand * msg)
{
  if (!msg) {
    return;
  }
  // action_label
  rosidl_runtime_c__String__fini(&msg->action_label);
  // waypoints
  robot_task_interfaces__msg__Waypoint__Sequence__fini(&msg->waypoints);
}

bool
robot_task_interfaces__msg__MoveCommand__are_equal(const robot_task_interfaces__msg__MoveCommand * lhs, const robot_task_interfaces__msg__MoveCommand * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // action_label
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->action_label), &(rhs->action_label)))
  {
    return false;
  }
  // waypoints
  if (!robot_task_interfaces__msg__Waypoint__Sequence__are_equal(
      &(lhs->waypoints), &(rhs->waypoints)))
  {
    return false;
  }
  return true;
}

bool
robot_task_interfaces__msg__MoveCommand__copy(
  const robot_task_interfaces__msg__MoveCommand * input,
  robot_task_interfaces__msg__MoveCommand * output)
{
  if (!input || !output) {
    return false;
  }
  // action_label
  if (!rosidl_runtime_c__String__copy(
      &(input->action_label), &(output->action_label)))
  {
    return false;
  }
  // waypoints
  if (!robot_task_interfaces__msg__Waypoint__Sequence__copy(
      &(input->waypoints), &(output->waypoints)))
  {
    return false;
  }
  return true;
}

robot_task_interfaces__msg__MoveCommand *
robot_task_interfaces__msg__MoveCommand__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  robot_task_interfaces__msg__MoveCommand * msg = (robot_task_interfaces__msg__MoveCommand *)allocator.allocate(sizeof(robot_task_interfaces__msg__MoveCommand), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(robot_task_interfaces__msg__MoveCommand));
  bool success = robot_task_interfaces__msg__MoveCommand__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
robot_task_interfaces__msg__MoveCommand__destroy(robot_task_interfaces__msg__MoveCommand * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    robot_task_interfaces__msg__MoveCommand__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
robot_task_interfaces__msg__MoveCommand__Sequence__init(robot_task_interfaces__msg__MoveCommand__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  robot_task_interfaces__msg__MoveCommand * data = NULL;

  if (size) {
    data = (robot_task_interfaces__msg__MoveCommand *)allocator.zero_allocate(size, sizeof(robot_task_interfaces__msg__MoveCommand), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = robot_task_interfaces__msg__MoveCommand__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        robot_task_interfaces__msg__MoveCommand__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
robot_task_interfaces__msg__MoveCommand__Sequence__fini(robot_task_interfaces__msg__MoveCommand__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      robot_task_interfaces__msg__MoveCommand__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

robot_task_interfaces__msg__MoveCommand__Sequence *
robot_task_interfaces__msg__MoveCommand__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  robot_task_interfaces__msg__MoveCommand__Sequence * array = (robot_task_interfaces__msg__MoveCommand__Sequence *)allocator.allocate(sizeof(robot_task_interfaces__msg__MoveCommand__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = robot_task_interfaces__msg__MoveCommand__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
robot_task_interfaces__msg__MoveCommand__Sequence__destroy(robot_task_interfaces__msg__MoveCommand__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    robot_task_interfaces__msg__MoveCommand__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
robot_task_interfaces__msg__MoveCommand__Sequence__are_equal(const robot_task_interfaces__msg__MoveCommand__Sequence * lhs, const robot_task_interfaces__msg__MoveCommand__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!robot_task_interfaces__msg__MoveCommand__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
robot_task_interfaces__msg__MoveCommand__Sequence__copy(
  const robot_task_interfaces__msg__MoveCommand__Sequence * input,
  robot_task_interfaces__msg__MoveCommand__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(robot_task_interfaces__msg__MoveCommand);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    robot_task_interfaces__msg__MoveCommand * data =
      (robot_task_interfaces__msg__MoveCommand *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!robot_task_interfaces__msg__MoveCommand__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          robot_task_interfaces__msg__MoveCommand__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!robot_task_interfaces__msg__MoveCommand__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
