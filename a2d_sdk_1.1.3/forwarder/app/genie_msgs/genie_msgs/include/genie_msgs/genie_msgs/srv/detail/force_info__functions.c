// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from genie_msgs:srv/ForceInfo.idl
// generated code does not contain a copyright notice
#include "genie_msgs/srv/detail/force_info__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"

// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"

bool
genie_msgs__srv__ForceInfo_Request__init(genie_msgs__srv__ForceInfo_Request * msg)
{
  if (!msg) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__init(&msg->header)) {
    genie_msgs__srv__ForceInfo_Request__fini(msg);
    return false;
  }
  // force_id
  return true;
}

void
genie_msgs__srv__ForceInfo_Request__fini(genie_msgs__srv__ForceInfo_Request * msg)
{
  if (!msg) {
    return;
  }
  // header
  std_msgs__msg__Header__fini(&msg->header);
  // force_id
}

bool
genie_msgs__srv__ForceInfo_Request__are_equal(const genie_msgs__srv__ForceInfo_Request * lhs, const genie_msgs__srv__ForceInfo_Request * rhs)
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
  // force_id
  if (lhs->force_id != rhs->force_id) {
    return false;
  }
  return true;
}

bool
genie_msgs__srv__ForceInfo_Request__copy(
  const genie_msgs__srv__ForceInfo_Request * input,
  genie_msgs__srv__ForceInfo_Request * output)
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
  // force_id
  output->force_id = input->force_id;
  return true;
}

genie_msgs__srv__ForceInfo_Request *
genie_msgs__srv__ForceInfo_Request__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__srv__ForceInfo_Request * msg = (genie_msgs__srv__ForceInfo_Request *)allocator.allocate(sizeof(genie_msgs__srv__ForceInfo_Request), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(genie_msgs__srv__ForceInfo_Request));
  bool success = genie_msgs__srv__ForceInfo_Request__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
genie_msgs__srv__ForceInfo_Request__destroy(genie_msgs__srv__ForceInfo_Request * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    genie_msgs__srv__ForceInfo_Request__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
genie_msgs__srv__ForceInfo_Request__Sequence__init(genie_msgs__srv__ForceInfo_Request__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__srv__ForceInfo_Request * data = NULL;

  if (size) {
    data = (genie_msgs__srv__ForceInfo_Request *)allocator.zero_allocate(size, sizeof(genie_msgs__srv__ForceInfo_Request), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = genie_msgs__srv__ForceInfo_Request__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        genie_msgs__srv__ForceInfo_Request__fini(&data[i - 1]);
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
genie_msgs__srv__ForceInfo_Request__Sequence__fini(genie_msgs__srv__ForceInfo_Request__Sequence * array)
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
      genie_msgs__srv__ForceInfo_Request__fini(&array->data[i]);
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

genie_msgs__srv__ForceInfo_Request__Sequence *
genie_msgs__srv__ForceInfo_Request__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__srv__ForceInfo_Request__Sequence * array = (genie_msgs__srv__ForceInfo_Request__Sequence *)allocator.allocate(sizeof(genie_msgs__srv__ForceInfo_Request__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = genie_msgs__srv__ForceInfo_Request__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
genie_msgs__srv__ForceInfo_Request__Sequence__destroy(genie_msgs__srv__ForceInfo_Request__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    genie_msgs__srv__ForceInfo_Request__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
genie_msgs__srv__ForceInfo_Request__Sequence__are_equal(const genie_msgs__srv__ForceInfo_Request__Sequence * lhs, const genie_msgs__srv__ForceInfo_Request__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!genie_msgs__srv__ForceInfo_Request__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
genie_msgs__srv__ForceInfo_Request__Sequence__copy(
  const genie_msgs__srv__ForceInfo_Request__Sequence * input,
  genie_msgs__srv__ForceInfo_Request__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(genie_msgs__srv__ForceInfo_Request);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    genie_msgs__srv__ForceInfo_Request * data =
      (genie_msgs__srv__ForceInfo_Request *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!genie_msgs__srv__ForceInfo_Request__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          genie_msgs__srv__ForceInfo_Request__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!genie_msgs__srv__ForceInfo_Request__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `res_header`
// already included above
// #include "std_msgs/msg/detail/header__functions.h"
// Member `work_zero_force_data`
// Member `tool_zero_force_data`
// Member `zero_force_data`
#include "rosidl_runtime_c/primitives_sequence_functions.h"

bool
genie_msgs__srv__ForceInfo_Response__init(genie_msgs__srv__ForceInfo_Response * msg)
{
  if (!msg) {
    return false;
  }
  // res_header
  if (!std_msgs__msg__Header__init(&msg->res_header)) {
    genie_msgs__srv__ForceInfo_Response__fini(msg);
    return false;
  }
  // exec_result
  // work_zero_force_data
  if (!rosidl_runtime_c__double__Sequence__init(&msg->work_zero_force_data, 0)) {
    genie_msgs__srv__ForceInfo_Response__fini(msg);
    return false;
  }
  // tool_zero_force_data
  if (!rosidl_runtime_c__double__Sequence__init(&msg->tool_zero_force_data, 0)) {
    genie_msgs__srv__ForceInfo_Response__fini(msg);
    return false;
  }
  // zero_force_data
  if (!rosidl_runtime_c__double__Sequence__init(&msg->zero_force_data, 0)) {
    genie_msgs__srv__ForceInfo_Response__fini(msg);
    return false;
  }
  return true;
}

void
genie_msgs__srv__ForceInfo_Response__fini(genie_msgs__srv__ForceInfo_Response * msg)
{
  if (!msg) {
    return;
  }
  // res_header
  std_msgs__msg__Header__fini(&msg->res_header);
  // exec_result
  // work_zero_force_data
  rosidl_runtime_c__double__Sequence__fini(&msg->work_zero_force_data);
  // tool_zero_force_data
  rosidl_runtime_c__double__Sequence__fini(&msg->tool_zero_force_data);
  // zero_force_data
  rosidl_runtime_c__double__Sequence__fini(&msg->zero_force_data);
}

bool
genie_msgs__srv__ForceInfo_Response__are_equal(const genie_msgs__srv__ForceInfo_Response * lhs, const genie_msgs__srv__ForceInfo_Response * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // res_header
  if (!std_msgs__msg__Header__are_equal(
      &(lhs->res_header), &(rhs->res_header)))
  {
    return false;
  }
  // exec_result
  if (lhs->exec_result != rhs->exec_result) {
    return false;
  }
  // work_zero_force_data
  if (!rosidl_runtime_c__double__Sequence__are_equal(
      &(lhs->work_zero_force_data), &(rhs->work_zero_force_data)))
  {
    return false;
  }
  // tool_zero_force_data
  if (!rosidl_runtime_c__double__Sequence__are_equal(
      &(lhs->tool_zero_force_data), &(rhs->tool_zero_force_data)))
  {
    return false;
  }
  // zero_force_data
  if (!rosidl_runtime_c__double__Sequence__are_equal(
      &(lhs->zero_force_data), &(rhs->zero_force_data)))
  {
    return false;
  }
  return true;
}

bool
genie_msgs__srv__ForceInfo_Response__copy(
  const genie_msgs__srv__ForceInfo_Response * input,
  genie_msgs__srv__ForceInfo_Response * output)
{
  if (!input || !output) {
    return false;
  }
  // res_header
  if (!std_msgs__msg__Header__copy(
      &(input->res_header), &(output->res_header)))
  {
    return false;
  }
  // exec_result
  output->exec_result = input->exec_result;
  // work_zero_force_data
  if (!rosidl_runtime_c__double__Sequence__copy(
      &(input->work_zero_force_data), &(output->work_zero_force_data)))
  {
    return false;
  }
  // tool_zero_force_data
  if (!rosidl_runtime_c__double__Sequence__copy(
      &(input->tool_zero_force_data), &(output->tool_zero_force_data)))
  {
    return false;
  }
  // zero_force_data
  if (!rosidl_runtime_c__double__Sequence__copy(
      &(input->zero_force_data), &(output->zero_force_data)))
  {
    return false;
  }
  return true;
}

genie_msgs__srv__ForceInfo_Response *
genie_msgs__srv__ForceInfo_Response__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__srv__ForceInfo_Response * msg = (genie_msgs__srv__ForceInfo_Response *)allocator.allocate(sizeof(genie_msgs__srv__ForceInfo_Response), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(genie_msgs__srv__ForceInfo_Response));
  bool success = genie_msgs__srv__ForceInfo_Response__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
genie_msgs__srv__ForceInfo_Response__destroy(genie_msgs__srv__ForceInfo_Response * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    genie_msgs__srv__ForceInfo_Response__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
genie_msgs__srv__ForceInfo_Response__Sequence__init(genie_msgs__srv__ForceInfo_Response__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__srv__ForceInfo_Response * data = NULL;

  if (size) {
    data = (genie_msgs__srv__ForceInfo_Response *)allocator.zero_allocate(size, sizeof(genie_msgs__srv__ForceInfo_Response), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = genie_msgs__srv__ForceInfo_Response__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        genie_msgs__srv__ForceInfo_Response__fini(&data[i - 1]);
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
genie_msgs__srv__ForceInfo_Response__Sequence__fini(genie_msgs__srv__ForceInfo_Response__Sequence * array)
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
      genie_msgs__srv__ForceInfo_Response__fini(&array->data[i]);
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

genie_msgs__srv__ForceInfo_Response__Sequence *
genie_msgs__srv__ForceInfo_Response__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__srv__ForceInfo_Response__Sequence * array = (genie_msgs__srv__ForceInfo_Response__Sequence *)allocator.allocate(sizeof(genie_msgs__srv__ForceInfo_Response__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = genie_msgs__srv__ForceInfo_Response__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
genie_msgs__srv__ForceInfo_Response__Sequence__destroy(genie_msgs__srv__ForceInfo_Response__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    genie_msgs__srv__ForceInfo_Response__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
genie_msgs__srv__ForceInfo_Response__Sequence__are_equal(const genie_msgs__srv__ForceInfo_Response__Sequence * lhs, const genie_msgs__srv__ForceInfo_Response__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!genie_msgs__srv__ForceInfo_Response__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
genie_msgs__srv__ForceInfo_Response__Sequence__copy(
  const genie_msgs__srv__ForceInfo_Response__Sequence * input,
  genie_msgs__srv__ForceInfo_Response__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(genie_msgs__srv__ForceInfo_Response);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    genie_msgs__srv__ForceInfo_Response * data =
      (genie_msgs__srv__ForceInfo_Response *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!genie_msgs__srv__ForceInfo_Response__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          genie_msgs__srv__ForceInfo_Response__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!genie_msgs__srv__ForceInfo_Response__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
