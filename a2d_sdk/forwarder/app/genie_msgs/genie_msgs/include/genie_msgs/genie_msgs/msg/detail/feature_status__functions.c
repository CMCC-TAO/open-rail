// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from genie_msgs:msg/FeatureStatus.idl
// generated code does not contain a copyright notice
#include "genie_msgs/msg/detail/feature_status__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"

bool
genie_msgs__msg__FeatureStatus__init(genie_msgs__msg__FeatureStatus * msg)
{
  if (!msg) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__init(&msg->header)) {
    genie_msgs__msg__FeatureStatus__fini(msg);
    return false;
  }
  // work_mode
  // feature_status
  return true;
}

void
genie_msgs__msg__FeatureStatus__fini(genie_msgs__msg__FeatureStatus * msg)
{
  if (!msg) {
    return;
  }
  // header
  std_msgs__msg__Header__fini(&msg->header);
  // work_mode
  // feature_status
}

bool
genie_msgs__msg__FeatureStatus__are_equal(const genie_msgs__msg__FeatureStatus * lhs, const genie_msgs__msg__FeatureStatus * rhs)
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
  // work_mode
  if (lhs->work_mode != rhs->work_mode) {
    return false;
  }
  // feature_status
  if (lhs->feature_status != rhs->feature_status) {
    return false;
  }
  return true;
}

bool
genie_msgs__msg__FeatureStatus__copy(
  const genie_msgs__msg__FeatureStatus * input,
  genie_msgs__msg__FeatureStatus * output)
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
  // work_mode
  output->work_mode = input->work_mode;
  // feature_status
  output->feature_status = input->feature_status;
  return true;
}

genie_msgs__msg__FeatureStatus *
genie_msgs__msg__FeatureStatus__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__FeatureStatus * msg = (genie_msgs__msg__FeatureStatus *)allocator.allocate(sizeof(genie_msgs__msg__FeatureStatus), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(genie_msgs__msg__FeatureStatus));
  bool success = genie_msgs__msg__FeatureStatus__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
genie_msgs__msg__FeatureStatus__destroy(genie_msgs__msg__FeatureStatus * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    genie_msgs__msg__FeatureStatus__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
genie_msgs__msg__FeatureStatus__Sequence__init(genie_msgs__msg__FeatureStatus__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__FeatureStatus * data = NULL;

  if (size) {
    data = (genie_msgs__msg__FeatureStatus *)allocator.zero_allocate(size, sizeof(genie_msgs__msg__FeatureStatus), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = genie_msgs__msg__FeatureStatus__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        genie_msgs__msg__FeatureStatus__fini(&data[i - 1]);
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
genie_msgs__msg__FeatureStatus__Sequence__fini(genie_msgs__msg__FeatureStatus__Sequence * array)
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
      genie_msgs__msg__FeatureStatus__fini(&array->data[i]);
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

genie_msgs__msg__FeatureStatus__Sequence *
genie_msgs__msg__FeatureStatus__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__FeatureStatus__Sequence * array = (genie_msgs__msg__FeatureStatus__Sequence *)allocator.allocate(sizeof(genie_msgs__msg__FeatureStatus__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = genie_msgs__msg__FeatureStatus__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
genie_msgs__msg__FeatureStatus__Sequence__destroy(genie_msgs__msg__FeatureStatus__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    genie_msgs__msg__FeatureStatus__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
genie_msgs__msg__FeatureStatus__Sequence__are_equal(const genie_msgs__msg__FeatureStatus__Sequence * lhs, const genie_msgs__msg__FeatureStatus__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!genie_msgs__msg__FeatureStatus__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
genie_msgs__msg__FeatureStatus__Sequence__copy(
  const genie_msgs__msg__FeatureStatus__Sequence * input,
  genie_msgs__msg__FeatureStatus__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(genie_msgs__msg__FeatureStatus);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    genie_msgs__msg__FeatureStatus * data =
      (genie_msgs__msg__FeatureStatus *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!genie_msgs__msg__FeatureStatus__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          genie_msgs__msg__FeatureStatus__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!genie_msgs__msg__FeatureStatus__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
