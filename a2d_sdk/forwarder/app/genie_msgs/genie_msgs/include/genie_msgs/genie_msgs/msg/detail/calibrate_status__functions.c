// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from genie_msgs:msg/CalibrateStatus.idl
// generated code does not contain a copyright notice
#include "genie_msgs/msg/detail/calibrate_status__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


bool
genie_msgs__msg__CalibrateStatus__init(genie_msgs__msg__CalibrateStatus * msg)
{
  if (!msg) {
    return false;
  }
  // structure_needs_at_least_one_member
  return true;
}

void
genie_msgs__msg__CalibrateStatus__fini(genie_msgs__msg__CalibrateStatus * msg)
{
  if (!msg) {
    return;
  }
  // structure_needs_at_least_one_member
}

bool
genie_msgs__msg__CalibrateStatus__are_equal(const genie_msgs__msg__CalibrateStatus * lhs, const genie_msgs__msg__CalibrateStatus * rhs)
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
genie_msgs__msg__CalibrateStatus__copy(
  const genie_msgs__msg__CalibrateStatus * input,
  genie_msgs__msg__CalibrateStatus * output)
{
  if (!input || !output) {
    return false;
  }
  // structure_needs_at_least_one_member
  output->structure_needs_at_least_one_member = input->structure_needs_at_least_one_member;
  return true;
}

genie_msgs__msg__CalibrateStatus *
genie_msgs__msg__CalibrateStatus__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__CalibrateStatus * msg = (genie_msgs__msg__CalibrateStatus *)allocator.allocate(sizeof(genie_msgs__msg__CalibrateStatus), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(genie_msgs__msg__CalibrateStatus));
  bool success = genie_msgs__msg__CalibrateStatus__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
genie_msgs__msg__CalibrateStatus__destroy(genie_msgs__msg__CalibrateStatus * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    genie_msgs__msg__CalibrateStatus__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
genie_msgs__msg__CalibrateStatus__Sequence__init(genie_msgs__msg__CalibrateStatus__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__CalibrateStatus * data = NULL;

  if (size) {
    data = (genie_msgs__msg__CalibrateStatus *)allocator.zero_allocate(size, sizeof(genie_msgs__msg__CalibrateStatus), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = genie_msgs__msg__CalibrateStatus__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        genie_msgs__msg__CalibrateStatus__fini(&data[i - 1]);
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
genie_msgs__msg__CalibrateStatus__Sequence__fini(genie_msgs__msg__CalibrateStatus__Sequence * array)
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
      genie_msgs__msg__CalibrateStatus__fini(&array->data[i]);
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

genie_msgs__msg__CalibrateStatus__Sequence *
genie_msgs__msg__CalibrateStatus__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__CalibrateStatus__Sequence * array = (genie_msgs__msg__CalibrateStatus__Sequence *)allocator.allocate(sizeof(genie_msgs__msg__CalibrateStatus__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = genie_msgs__msg__CalibrateStatus__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
genie_msgs__msg__CalibrateStatus__Sequence__destroy(genie_msgs__msg__CalibrateStatus__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    genie_msgs__msg__CalibrateStatus__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
genie_msgs__msg__CalibrateStatus__Sequence__are_equal(const genie_msgs__msg__CalibrateStatus__Sequence * lhs, const genie_msgs__msg__CalibrateStatus__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!genie_msgs__msg__CalibrateStatus__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
genie_msgs__msg__CalibrateStatus__Sequence__copy(
  const genie_msgs__msg__CalibrateStatus__Sequence * input,
  genie_msgs__msg__CalibrateStatus__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(genie_msgs__msg__CalibrateStatus);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    genie_msgs__msg__CalibrateStatus * data =
      (genie_msgs__msg__CalibrateStatus *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!genie_msgs__msg__CalibrateStatus__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          genie_msgs__msg__CalibrateStatus__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!genie_msgs__msg__CalibrateStatus__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
