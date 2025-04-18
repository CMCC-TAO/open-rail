// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from genie_msgs:msg/AGVTargetStation.idl
// generated code does not contain a copyright notice
#include "genie_msgs/msg/detail/agv_target_station__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"
// Member `station_name`
#include "rosidl_runtime_c/string_functions.h"

bool
genie_msgs__msg__AGVTargetStation__init(genie_msgs__msg__AGVTargetStation * msg)
{
  if (!msg) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__init(&msg->header)) {
    genie_msgs__msg__AGVTargetStation__fini(msg);
    return false;
  }
  // station_id
  // station_name
  if (!rosidl_runtime_c__String__init(&msg->station_name)) {
    genie_msgs__msg__AGVTargetStation__fini(msg);
    return false;
  }
  // station_action
  return true;
}

void
genie_msgs__msg__AGVTargetStation__fini(genie_msgs__msg__AGVTargetStation * msg)
{
  if (!msg) {
    return;
  }
  // header
  std_msgs__msg__Header__fini(&msg->header);
  // station_id
  // station_name
  rosidl_runtime_c__String__fini(&msg->station_name);
  // station_action
}

bool
genie_msgs__msg__AGVTargetStation__are_equal(const genie_msgs__msg__AGVTargetStation * lhs, const genie_msgs__msg__AGVTargetStation * rhs)
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
  // station_id
  if (lhs->station_id != rhs->station_id) {
    return false;
  }
  // station_name
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->station_name), &(rhs->station_name)))
  {
    return false;
  }
  // station_action
  if (lhs->station_action != rhs->station_action) {
    return false;
  }
  return true;
}

bool
genie_msgs__msg__AGVTargetStation__copy(
  const genie_msgs__msg__AGVTargetStation * input,
  genie_msgs__msg__AGVTargetStation * output)
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
  // station_id
  output->station_id = input->station_id;
  // station_name
  if (!rosidl_runtime_c__String__copy(
      &(input->station_name), &(output->station_name)))
  {
    return false;
  }
  // station_action
  output->station_action = input->station_action;
  return true;
}

genie_msgs__msg__AGVTargetStation *
genie_msgs__msg__AGVTargetStation__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__AGVTargetStation * msg = (genie_msgs__msg__AGVTargetStation *)allocator.allocate(sizeof(genie_msgs__msg__AGVTargetStation), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(genie_msgs__msg__AGVTargetStation));
  bool success = genie_msgs__msg__AGVTargetStation__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
genie_msgs__msg__AGVTargetStation__destroy(genie_msgs__msg__AGVTargetStation * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    genie_msgs__msg__AGVTargetStation__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
genie_msgs__msg__AGVTargetStation__Sequence__init(genie_msgs__msg__AGVTargetStation__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__AGVTargetStation * data = NULL;

  if (size) {
    data = (genie_msgs__msg__AGVTargetStation *)allocator.zero_allocate(size, sizeof(genie_msgs__msg__AGVTargetStation), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = genie_msgs__msg__AGVTargetStation__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        genie_msgs__msg__AGVTargetStation__fini(&data[i - 1]);
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
genie_msgs__msg__AGVTargetStation__Sequence__fini(genie_msgs__msg__AGVTargetStation__Sequence * array)
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
      genie_msgs__msg__AGVTargetStation__fini(&array->data[i]);
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

genie_msgs__msg__AGVTargetStation__Sequence *
genie_msgs__msg__AGVTargetStation__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__AGVTargetStation__Sequence * array = (genie_msgs__msg__AGVTargetStation__Sequence *)allocator.allocate(sizeof(genie_msgs__msg__AGVTargetStation__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = genie_msgs__msg__AGVTargetStation__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
genie_msgs__msg__AGVTargetStation__Sequence__destroy(genie_msgs__msg__AGVTargetStation__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    genie_msgs__msg__AGVTargetStation__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
genie_msgs__msg__AGVTargetStation__Sequence__are_equal(const genie_msgs__msg__AGVTargetStation__Sequence * lhs, const genie_msgs__msg__AGVTargetStation__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!genie_msgs__msg__AGVTargetStation__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
genie_msgs__msg__AGVTargetStation__Sequence__copy(
  const genie_msgs__msg__AGVTargetStation__Sequence * input,
  genie_msgs__msg__AGVTargetStation__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(genie_msgs__msg__AGVTargetStation);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    genie_msgs__msg__AGVTargetStation * data =
      (genie_msgs__msg__AGVTargetStation *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!genie_msgs__msg__AGVTargetStation__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          genie_msgs__msg__AGVTargetStation__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!genie_msgs__msg__AGVTargetStation__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
