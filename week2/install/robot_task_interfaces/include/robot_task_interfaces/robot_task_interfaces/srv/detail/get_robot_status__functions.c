// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from robot_task_interfaces:srv/GetRobotStatus.idl
// generated code does not contain a copyright notice
#include "robot_task_interfaces/srv/detail/get_robot_status__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"

bool
robot_task_interfaces__srv__GetRobotStatus_Request__init(robot_task_interfaces__srv__GetRobotStatus_Request * msg)
{
  if (!msg) {
    return false;
  }
  // structure_needs_at_least_one_member
  return true;
}

void
robot_task_interfaces__srv__GetRobotStatus_Request__fini(robot_task_interfaces__srv__GetRobotStatus_Request * msg)
{
  if (!msg) {
    return;
  }
  // structure_needs_at_least_one_member
}

bool
robot_task_interfaces__srv__GetRobotStatus_Request__are_equal(const robot_task_interfaces__srv__GetRobotStatus_Request * lhs, const robot_task_interfaces__srv__GetRobotStatus_Request * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // structure_needs_at_least_one_member
  if (lhs->structure_needs_at_least_one_member != rhs->structure_needs_at_least_one_member) {
    return false;
  }
  return true;
}

bool
robot_task_interfaces__srv__GetRobotStatus_Request__copy(
  const robot_task_interfaces__srv__GetRobotStatus_Request * input,
  robot_task_interfaces__srv__GetRobotStatus_Request * output)
{
  if (!input || !output) {
    return false;
  }
  // structure_needs_at_least_one_member
  output->structure_needs_at_least_one_member = input->structure_needs_at_least_one_member;
  return true;
}

robot_task_interfaces__srv__GetRobotStatus_Request *
robot_task_interfaces__srv__GetRobotStatus_Request__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  robot_task_interfaces__srv__GetRobotStatus_Request * msg = (robot_task_interfaces__srv__GetRobotStatus_Request *)allocator.allocate(sizeof(robot_task_interfaces__srv__GetRobotStatus_Request), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(robot_task_interfaces__srv__GetRobotStatus_Request));
  bool success = robot_task_interfaces__srv__GetRobotStatus_Request__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
robot_task_interfaces__srv__GetRobotStatus_Request__destroy(robot_task_interfaces__srv__GetRobotStatus_Request * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    robot_task_interfaces__srv__GetRobotStatus_Request__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
robot_task_interfaces__srv__GetRobotStatus_Request__Sequence__init(robot_task_interfaces__srv__GetRobotStatus_Request__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  robot_task_interfaces__srv__GetRobotStatus_Request * data = NULL;

  if (size) {
    data = (robot_task_interfaces__srv__GetRobotStatus_Request *)allocator.zero_allocate(size, sizeof(robot_task_interfaces__srv__GetRobotStatus_Request), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = robot_task_interfaces__srv__GetRobotStatus_Request__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        robot_task_interfaces__srv__GetRobotStatus_Request__fini(&data[i - 1]);
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
robot_task_interfaces__srv__GetRobotStatus_Request__Sequence__fini(robot_task_interfaces__srv__GetRobotStatus_Request__Sequence * array)
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
      robot_task_interfaces__srv__GetRobotStatus_Request__fini(&array->data[i]);
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

robot_task_interfaces__srv__GetRobotStatus_Request__Sequence *
robot_task_interfaces__srv__GetRobotStatus_Request__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  robot_task_interfaces__srv__GetRobotStatus_Request__Sequence * array = (robot_task_interfaces__srv__GetRobotStatus_Request__Sequence *)allocator.allocate(sizeof(robot_task_interfaces__srv__GetRobotStatus_Request__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = robot_task_interfaces__srv__GetRobotStatus_Request__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
robot_task_interfaces__srv__GetRobotStatus_Request__Sequence__destroy(robot_task_interfaces__srv__GetRobotStatus_Request__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    robot_task_interfaces__srv__GetRobotStatus_Request__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
robot_task_interfaces__srv__GetRobotStatus_Request__Sequence__are_equal(const robot_task_interfaces__srv__GetRobotStatus_Request__Sequence * lhs, const robot_task_interfaces__srv__GetRobotStatus_Request__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!robot_task_interfaces__srv__GetRobotStatus_Request__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
robot_task_interfaces__srv__GetRobotStatus_Request__Sequence__copy(
  const robot_task_interfaces__srv__GetRobotStatus_Request__Sequence * input,
  robot_task_interfaces__srv__GetRobotStatus_Request__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(robot_task_interfaces__srv__GetRobotStatus_Request);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    robot_task_interfaces__srv__GetRobotStatus_Request * data =
      (robot_task_interfaces__srv__GetRobotStatus_Request *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!robot_task_interfaces__srv__GetRobotStatus_Request__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          robot_task_interfaces__srv__GetRobotStatus_Request__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!robot_task_interfaces__srv__GetRobotStatus_Request__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `status`
// Member `current_action`
#include "rosidl_runtime_c/string_functions.h"

bool
robot_task_interfaces__srv__GetRobotStatus_Response__init(robot_task_interfaces__srv__GetRobotStatus_Response * msg)
{
  if (!msg) {
    return false;
  }
  // status
  if (!rosidl_runtime_c__String__init(&msg->status)) {
    robot_task_interfaces__srv__GetRobotStatus_Response__fini(msg);
    return false;
  }
  // current_action
  if (!rosidl_runtime_c__String__init(&msg->current_action)) {
    robot_task_interfaces__srv__GetRobotStatus_Response__fini(msg);
    return false;
  }
  // elapsed_time
  return true;
}

void
robot_task_interfaces__srv__GetRobotStatus_Response__fini(robot_task_interfaces__srv__GetRobotStatus_Response * msg)
{
  if (!msg) {
    return;
  }
  // status
  rosidl_runtime_c__String__fini(&msg->status);
  // current_action
  rosidl_runtime_c__String__fini(&msg->current_action);
  // elapsed_time
}

bool
robot_task_interfaces__srv__GetRobotStatus_Response__are_equal(const robot_task_interfaces__srv__GetRobotStatus_Response * lhs, const robot_task_interfaces__srv__GetRobotStatus_Response * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // status
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->status), &(rhs->status)))
  {
    return false;
  }
  // current_action
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->current_action), &(rhs->current_action)))
  {
    return false;
  }
  // elapsed_time
  if (lhs->elapsed_time != rhs->elapsed_time) {
    return false;
  }
  return true;
}

bool
robot_task_interfaces__srv__GetRobotStatus_Response__copy(
  const robot_task_interfaces__srv__GetRobotStatus_Response * input,
  robot_task_interfaces__srv__GetRobotStatus_Response * output)
{
  if (!input || !output) {
    return false;
  }
  // status
  if (!rosidl_runtime_c__String__copy(
      &(input->status), &(output->status)))
  {
    return false;
  }
  // current_action
  if (!rosidl_runtime_c__String__copy(
      &(input->current_action), &(output->current_action)))
  {
    return false;
  }
  // elapsed_time
  output->elapsed_time = input->elapsed_time;
  return true;
}

robot_task_interfaces__srv__GetRobotStatus_Response *
robot_task_interfaces__srv__GetRobotStatus_Response__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  robot_task_interfaces__srv__GetRobotStatus_Response * msg = (robot_task_interfaces__srv__GetRobotStatus_Response *)allocator.allocate(sizeof(robot_task_interfaces__srv__GetRobotStatus_Response), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(robot_task_interfaces__srv__GetRobotStatus_Response));
  bool success = robot_task_interfaces__srv__GetRobotStatus_Response__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
robot_task_interfaces__srv__GetRobotStatus_Response__destroy(robot_task_interfaces__srv__GetRobotStatus_Response * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    robot_task_interfaces__srv__GetRobotStatus_Response__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
robot_task_interfaces__srv__GetRobotStatus_Response__Sequence__init(robot_task_interfaces__srv__GetRobotStatus_Response__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  robot_task_interfaces__srv__GetRobotStatus_Response * data = NULL;

  if (size) {
    data = (robot_task_interfaces__srv__GetRobotStatus_Response *)allocator.zero_allocate(size, sizeof(robot_task_interfaces__srv__GetRobotStatus_Response), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = robot_task_interfaces__srv__GetRobotStatus_Response__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        robot_task_interfaces__srv__GetRobotStatus_Response__fini(&data[i - 1]);
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
robot_task_interfaces__srv__GetRobotStatus_Response__Sequence__fini(robot_task_interfaces__srv__GetRobotStatus_Response__Sequence * array)
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
      robot_task_interfaces__srv__GetRobotStatus_Response__fini(&array->data[i]);
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

robot_task_interfaces__srv__GetRobotStatus_Response__Sequence *
robot_task_interfaces__srv__GetRobotStatus_Response__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  robot_task_interfaces__srv__GetRobotStatus_Response__Sequence * array = (robot_task_interfaces__srv__GetRobotStatus_Response__Sequence *)allocator.allocate(sizeof(robot_task_interfaces__srv__GetRobotStatus_Response__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = robot_task_interfaces__srv__GetRobotStatus_Response__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
robot_task_interfaces__srv__GetRobotStatus_Response__Sequence__destroy(robot_task_interfaces__srv__GetRobotStatus_Response__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    robot_task_interfaces__srv__GetRobotStatus_Response__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
robot_task_interfaces__srv__GetRobotStatus_Response__Sequence__are_equal(const robot_task_interfaces__srv__GetRobotStatus_Response__Sequence * lhs, const robot_task_interfaces__srv__GetRobotStatus_Response__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!robot_task_interfaces__srv__GetRobotStatus_Response__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
robot_task_interfaces__srv__GetRobotStatus_Response__Sequence__copy(
  const robot_task_interfaces__srv__GetRobotStatus_Response__Sequence * input,
  robot_task_interfaces__srv__GetRobotStatus_Response__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(robot_task_interfaces__srv__GetRobotStatus_Response);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    robot_task_interfaces__srv__GetRobotStatus_Response * data =
      (robot_task_interfaces__srv__GetRobotStatus_Response *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!robot_task_interfaces__srv__GetRobotStatus_Response__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          robot_task_interfaces__srv__GetRobotStatus_Response__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!robot_task_interfaces__srv__GetRobotStatus_Response__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
