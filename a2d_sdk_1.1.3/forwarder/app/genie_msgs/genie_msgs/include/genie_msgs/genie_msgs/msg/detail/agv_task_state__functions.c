// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from genie_msgs:msg/AGVTaskState.idl
// generated code does not contain a copyright notice
#include "genie_msgs/msg/detail/agv_task_state__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"
// Member `task_reqid`
#include "rosidl_runtime_c/string_functions.h"

bool
genie_msgs__msg__AGVTaskState__init(genie_msgs__msg__AGVTaskState * msg)
{
  if (!msg) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__init(&msg->header)) {
    genie_msgs__msg__AGVTaskState__fini(msg);
    return false;
  }
  // task_uuid
  // task_reqid
  if (!rosidl_runtime_c__String__init(&msg->task_reqid)) {
    genie_msgs__msg__AGVTaskState__fini(msg);
    return false;
  }
  // curr_station_idx
  // finish_state
  return true;
}

void
genie_msgs__msg__AGVTaskState__fini(genie_msgs__msg__AGVTaskState * msg)
{
  if (!msg) {
    return;
  }
  // header
  std_msgs__msg__Header__fini(&msg->header);
  // task_uuid
  // task_reqid
  rosidl_runtime_c__String__fini(&msg->task_reqid);
  // curr_station_idx
  // finish_state
}

bool
genie_msgs__msg__AGVTaskState__are_equal(const genie_msgs__msg__AGVTaskState * lhs, const genie_msgs__msg__AGVTaskState * rhs)
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
  // task_uuid
  if (lhs->task_uuid != rhs->task_uuid) {
    return false;
  }
  // task_reqid
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->task_reqid), &(rhs->task_reqid)))
  {
    return false;
  }
  // curr_station_idx
  if (lhs->curr_station_idx != rhs->curr_station_idx) {
    return false;
  }
  // finish_state
  if (lhs->finish_state != rhs->finish_state) {
    return false;
  }
  return true;
}

bool
genie_msgs__msg__AGVTaskState__copy(
  const genie_msgs__msg__AGVTaskState * input,
  genie_msgs__msg__AGVTaskState * output)
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
  // task_uuid
  output->task_uuid = input->task_uuid;
  // task_reqid
  if (!rosidl_runtime_c__String__copy(
      &(input->task_reqid), &(output->task_reqid)))
  {
    return false;
  }
  // curr_station_idx
  output->curr_station_idx = input->curr_station_idx;
  // finish_state
  output->finish_state = input->finish_state;
  return true;
}

genie_msgs__msg__AGVTaskState *
genie_msgs__msg__AGVTaskState__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__AGVTaskState * msg = (genie_msgs__msg__AGVTaskState *)allocator.allocate(sizeof(genie_msgs__msg__AGVTaskState), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(genie_msgs__msg__AGVTaskState));
  bool success = genie_msgs__msg__AGVTaskState__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
genie_msgs__msg__AGVTaskState__destroy(genie_msgs__msg__AGVTaskState * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    genie_msgs__msg__AGVTaskState__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
genie_msgs__msg__AGVTaskState__Sequence__init(genie_msgs__msg__AGVTaskState__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__AGVTaskState * data = NULL;

  if (size) {
    data = (genie_msgs__msg__AGVTaskState *)allocator.zero_allocate(size, sizeof(genie_msgs__msg__AGVTaskState), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = genie_msgs__msg__AGVTaskState__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        genie_msgs__msg__AGVTaskState__fini(&data[i - 1]);
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
genie_msgs__msg__AGVTaskState__Sequence__fini(genie_msgs__msg__AGVTaskState__Sequence * array)
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
      genie_msgs__msg__AGVTaskState__fini(&array->data[i]);
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

genie_msgs__msg__AGVTaskState__Sequence *
genie_msgs__msg__AGVTaskState__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__AGVTaskState__Sequence * array = (genie_msgs__msg__AGVTaskState__Sequence *)allocator.allocate(sizeof(genie_msgs__msg__AGVTaskState__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = genie_msgs__msg__AGVTaskState__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
genie_msgs__msg__AGVTaskState__Sequence__destroy(genie_msgs__msg__AGVTaskState__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    genie_msgs__msg__AGVTaskState__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
genie_msgs__msg__AGVTaskState__Sequence__are_equal(const genie_msgs__msg__AGVTaskState__Sequence * lhs, const genie_msgs__msg__AGVTaskState__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!genie_msgs__msg__AGVTaskState__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
genie_msgs__msg__AGVTaskState__Sequence__copy(
  const genie_msgs__msg__AGVTaskState__Sequence * input,
  genie_msgs__msg__AGVTaskState__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(genie_msgs__msg__AGVTaskState);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    genie_msgs__msg__AGVTaskState * data =
      (genie_msgs__msg__AGVTaskState *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!genie_msgs__msg__AGVTaskState__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          genie_msgs__msg__AGVTaskState__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!genie_msgs__msg__AGVTaskState__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
