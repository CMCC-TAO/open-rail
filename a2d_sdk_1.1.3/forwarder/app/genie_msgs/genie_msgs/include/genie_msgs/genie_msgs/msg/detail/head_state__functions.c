// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from genie_msgs:msg/HeadState.idl
// generated code does not contain a copyright notice
#include "genie_msgs/msg/detail/head_state__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"
// Member `motor_states`
#include "genie_msgs/msg/detail/motor_state__functions.h"
// Member `name`
#include "rosidl_runtime_c/string_functions.h"

bool
genie_msgs__msg__HeadState__init(genie_msgs__msg__HeadState * msg)
{
  if (!msg) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__init(&msg->header)) {
    genie_msgs__msg__HeadState__fini(msg);
    return false;
  }
  // motor_states
  if (!genie_msgs__msg__MotorState__Sequence__init(&msg->motor_states, 0)) {
    genie_msgs__msg__HeadState__fini(msg);
    return false;
  }
  // name
  if (!rosidl_runtime_c__String__Sequence__init(&msg->name, 0)) {
    genie_msgs__msg__HeadState__fini(msg);
    return false;
  }
  return true;
}

void
genie_msgs__msg__HeadState__fini(genie_msgs__msg__HeadState * msg)
{
  if (!msg) {
    return;
  }
  // header
  std_msgs__msg__Header__fini(&msg->header);
  // motor_states
  genie_msgs__msg__MotorState__Sequence__fini(&msg->motor_states);
  // name
  rosidl_runtime_c__String__Sequence__fini(&msg->name);
}

bool
genie_msgs__msg__HeadState__are_equal(const genie_msgs__msg__HeadState * lhs, const genie_msgs__msg__HeadState * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__are_equal(
      &(lhs->header), &(rhs->header)))
  {
    return false;
  }
  // motor_states
  if (!genie_msgs__msg__MotorState__Sequence__are_equal(
      &(lhs->motor_states), &(rhs->motor_states)))
  {
    return false;
  }
  // name
  if (!rosidl_runtime_c__String__Sequence__are_equal(
      &(lhs->name), &(rhs->name)))
  {
    return false;
  }
  return true;
}

bool
genie_msgs__msg__HeadState__copy(
  const genie_msgs__msg__HeadState * input,
  genie_msgs__msg__HeadState * output)
{
  if (!input || !output) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__copy(
      &(input->header), &(output->header)))
  {
    return false;
  }
  // motor_states
  if (!genie_msgs__msg__MotorState__Sequence__copy(
      &(input->motor_states), &(output->motor_states)))
  {
    return false;
  }
  // name
  if (!rosidl_runtime_c__String__Sequence__copy(
      &(input->name), &(output->name)))
  {
    return false;
  }
  return true;
}

genie_msgs__msg__HeadState *
genie_msgs__msg__HeadState__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__HeadState * msg = (genie_msgs__msg__HeadState *)allocator.allocate(sizeof(genie_msgs__msg__HeadState), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(genie_msgs__msg__HeadState));
  bool success = genie_msgs__msg__HeadState__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
genie_msgs__msg__HeadState__destroy(genie_msgs__msg__HeadState * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    genie_msgs__msg__HeadState__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
genie_msgs__msg__HeadState__Sequence__init(genie_msgs__msg__HeadState__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__HeadState * data = NULL;

  if (size) {
    data = (genie_msgs__msg__HeadState *)allocator.zero_allocate(size, sizeof(genie_msgs__msg__HeadState), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = genie_msgs__msg__HeadState__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        genie_msgs__msg__HeadState__fini(&data[i - 1]);
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
genie_msgs__msg__HeadState__Sequence__fini(genie_msgs__msg__HeadState__Sequence * array)
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
      genie_msgs__msg__HeadState__fini(&array->data[i]);
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

genie_msgs__msg__HeadState__Sequence *
genie_msgs__msg__HeadState__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__HeadState__Sequence * array = (genie_msgs__msg__HeadState__Sequence *)allocator.allocate(sizeof(genie_msgs__msg__HeadState__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = genie_msgs__msg__HeadState__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
genie_msgs__msg__HeadState__Sequence__destroy(genie_msgs__msg__HeadState__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    genie_msgs__msg__HeadState__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
genie_msgs__msg__HeadState__Sequence__are_equal(const genie_msgs__msg__HeadState__Sequence * lhs, const genie_msgs__msg__HeadState__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!genie_msgs__msg__HeadState__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
genie_msgs__msg__HeadState__Sequence__copy(
  const genie_msgs__msg__HeadState__Sequence * input,
  genie_msgs__msg__HeadState__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(genie_msgs__msg__HeadState);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    genie_msgs__msg__HeadState * data =
      (genie_msgs__msg__HeadState *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!genie_msgs__msg__HeadState__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          genie_msgs__msg__HeadState__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!genie_msgs__msg__HeadState__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
