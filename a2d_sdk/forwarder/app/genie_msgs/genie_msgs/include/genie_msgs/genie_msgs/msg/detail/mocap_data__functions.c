// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from genie_msgs:msg/MocapData.idl
// generated code does not contain a copyright notice
#include "genie_msgs/msg/detail/mocap_data__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"
// Member `mocap_joint_states`
#include "genie_msgs/msg/detail/mocap_joint_state__functions.h"

bool
genie_msgs__msg__MocapData__init(genie_msgs__msg__MocapData * msg)
{
  if (!msg) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__init(&msg->header)) {
    genie_msgs__msg__MocapData__fini(msg);
    return false;
  }
  // status
  // err_code
  // mocap_joint_states
  if (!genie_msgs__msg__MocapJointState__Sequence__init(&msg->mocap_joint_states, 0)) {
    genie_msgs__msg__MocapData__fini(msg);
    return false;
  }
  return true;
}

void
genie_msgs__msg__MocapData__fini(genie_msgs__msg__MocapData * msg)
{
  if (!msg) {
    return;
  }
  // header
  std_msgs__msg__Header__fini(&msg->header);
  // status
  // err_code
  // mocap_joint_states
  genie_msgs__msg__MocapJointState__Sequence__fini(&msg->mocap_joint_states);
}

bool
genie_msgs__msg__MocapData__are_equal(const genie_msgs__msg__MocapData * lhs, const genie_msgs__msg__MocapData * rhs)
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
  // status
  if (lhs->status != rhs->status) {
    return false;
  }
  // err_code
  if (lhs->err_code != rhs->err_code) {
    return false;
  }
  // mocap_joint_states
  if (!genie_msgs__msg__MocapJointState__Sequence__are_equal(
      &(lhs->mocap_joint_states), &(rhs->mocap_joint_states)))
  {
    return false;
  }
  return true;
}

bool
genie_msgs__msg__MocapData__copy(
  const genie_msgs__msg__MocapData * input,
  genie_msgs__msg__MocapData * output)
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
  // status
  output->status = input->status;
  // err_code
  output->err_code = input->err_code;
  // mocap_joint_states
  if (!genie_msgs__msg__MocapJointState__Sequence__copy(
      &(input->mocap_joint_states), &(output->mocap_joint_states)))
  {
    return false;
  }
  return true;
}

genie_msgs__msg__MocapData *
genie_msgs__msg__MocapData__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__MocapData * msg = (genie_msgs__msg__MocapData *)allocator.allocate(sizeof(genie_msgs__msg__MocapData), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(genie_msgs__msg__MocapData));
  bool success = genie_msgs__msg__MocapData__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
genie_msgs__msg__MocapData__destroy(genie_msgs__msg__MocapData * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    genie_msgs__msg__MocapData__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
genie_msgs__msg__MocapData__Sequence__init(genie_msgs__msg__MocapData__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__MocapData * data = NULL;

  if (size) {
    data = (genie_msgs__msg__MocapData *)allocator.zero_allocate(size, sizeof(genie_msgs__msg__MocapData), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = genie_msgs__msg__MocapData__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        genie_msgs__msg__MocapData__fini(&data[i - 1]);
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
genie_msgs__msg__MocapData__Sequence__fini(genie_msgs__msg__MocapData__Sequence * array)
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
      genie_msgs__msg__MocapData__fini(&array->data[i]);
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

genie_msgs__msg__MocapData__Sequence *
genie_msgs__msg__MocapData__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__MocapData__Sequence * array = (genie_msgs__msg__MocapData__Sequence *)allocator.allocate(sizeof(genie_msgs__msg__MocapData__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = genie_msgs__msg__MocapData__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
genie_msgs__msg__MocapData__Sequence__destroy(genie_msgs__msg__MocapData__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    genie_msgs__msg__MocapData__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
genie_msgs__msg__MocapData__Sequence__are_equal(const genie_msgs__msg__MocapData__Sequence * lhs, const genie_msgs__msg__MocapData__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!genie_msgs__msg__MocapData__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
genie_msgs__msg__MocapData__Sequence__copy(
  const genie_msgs__msg__MocapData__Sequence * input,
  genie_msgs__msg__MocapData__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(genie_msgs__msg__MocapData);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    genie_msgs__msg__MocapData * data =
      (genie_msgs__msg__MocapData *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!genie_msgs__msg__MocapData__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          genie_msgs__msg__MocapData__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!genie_msgs__msg__MocapData__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
