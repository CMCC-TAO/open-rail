// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from genie_msgs:srv/FeatSetWorkMode.idl
// generated code does not contain a copyright notice
#include "genie_msgs/srv/detail/feat_set_work_mode__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"

// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"

bool
genie_msgs__srv__FeatSetWorkMode_Request__init(genie_msgs__srv__FeatSetWorkMode_Request * msg)
{
  if (!msg) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__init(&msg->header)) {
    genie_msgs__srv__FeatSetWorkMode_Request__fini(msg);
    return false;
  }
  // work_mode
  return true;
}

void
genie_msgs__srv__FeatSetWorkMode_Request__fini(genie_msgs__srv__FeatSetWorkMode_Request * msg)
{
  if (!msg) {
    return;
  }
  // header
  std_msgs__msg__Header__fini(&msg->header);
  // work_mode
}

bool
genie_msgs__srv__FeatSetWorkMode_Request__are_equal(const genie_msgs__srv__FeatSetWorkMode_Request * lhs, const genie_msgs__srv__FeatSetWorkMode_Request * rhs)
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
  return true;
}

bool
genie_msgs__srv__FeatSetWorkMode_Request__copy(
  const genie_msgs__srv__FeatSetWorkMode_Request * input,
  genie_msgs__srv__FeatSetWorkMode_Request * output)
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
  return true;
}

genie_msgs__srv__FeatSetWorkMode_Request *
genie_msgs__srv__FeatSetWorkMode_Request__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__srv__FeatSetWorkMode_Request * msg = (genie_msgs__srv__FeatSetWorkMode_Request *)allocator.allocate(sizeof(genie_msgs__srv__FeatSetWorkMode_Request), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(genie_msgs__srv__FeatSetWorkMode_Request));
  bool success = genie_msgs__srv__FeatSetWorkMode_Request__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
genie_msgs__srv__FeatSetWorkMode_Request__destroy(genie_msgs__srv__FeatSetWorkMode_Request * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    genie_msgs__srv__FeatSetWorkMode_Request__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
genie_msgs__srv__FeatSetWorkMode_Request__Sequence__init(genie_msgs__srv__FeatSetWorkMode_Request__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__srv__FeatSetWorkMode_Request * data = NULL;

  if (size) {
    data = (genie_msgs__srv__FeatSetWorkMode_Request *)allocator.zero_allocate(size, sizeof(genie_msgs__srv__FeatSetWorkMode_Request), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = genie_msgs__srv__FeatSetWorkMode_Request__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        genie_msgs__srv__FeatSetWorkMode_Request__fini(&data[i - 1]);
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
genie_msgs__srv__FeatSetWorkMode_Request__Sequence__fini(genie_msgs__srv__FeatSetWorkMode_Request__Sequence * array)
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
      genie_msgs__srv__FeatSetWorkMode_Request__fini(&array->data[i]);
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

genie_msgs__srv__FeatSetWorkMode_Request__Sequence *
genie_msgs__srv__FeatSetWorkMode_Request__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__srv__FeatSetWorkMode_Request__Sequence * array = (genie_msgs__srv__FeatSetWorkMode_Request__Sequence *)allocator.allocate(sizeof(genie_msgs__srv__FeatSetWorkMode_Request__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = genie_msgs__srv__FeatSetWorkMode_Request__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
genie_msgs__srv__FeatSetWorkMode_Request__Sequence__destroy(genie_msgs__srv__FeatSetWorkMode_Request__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    genie_msgs__srv__FeatSetWorkMode_Request__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
genie_msgs__srv__FeatSetWorkMode_Request__Sequence__are_equal(const genie_msgs__srv__FeatSetWorkMode_Request__Sequence * lhs, const genie_msgs__srv__FeatSetWorkMode_Request__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!genie_msgs__srv__FeatSetWorkMode_Request__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
genie_msgs__srv__FeatSetWorkMode_Request__Sequence__copy(
  const genie_msgs__srv__FeatSetWorkMode_Request__Sequence * input,
  genie_msgs__srv__FeatSetWorkMode_Request__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(genie_msgs__srv__FeatSetWorkMode_Request);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    genie_msgs__srv__FeatSetWorkMode_Request * data =
      (genie_msgs__srv__FeatSetWorkMode_Request *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!genie_msgs__srv__FeatSetWorkMode_Request__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          genie_msgs__srv__FeatSetWorkMode_Request__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!genie_msgs__srv__FeatSetWorkMode_Request__copy(
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

bool
genie_msgs__srv__FeatSetWorkMode_Response__init(genie_msgs__srv__FeatSetWorkMode_Response * msg)
{
  if (!msg) {
    return false;
  }
  // res_header
  if (!std_msgs__msg__Header__init(&msg->res_header)) {
    genie_msgs__srv__FeatSetWorkMode_Response__fini(msg);
    return false;
  }
  // exec_result
  return true;
}

void
genie_msgs__srv__FeatSetWorkMode_Response__fini(genie_msgs__srv__FeatSetWorkMode_Response * msg)
{
  if (!msg) {
    return;
  }
  // res_header
  std_msgs__msg__Header__fini(&msg->res_header);
  // exec_result
}

bool
genie_msgs__srv__FeatSetWorkMode_Response__are_equal(const genie_msgs__srv__FeatSetWorkMode_Response * lhs, const genie_msgs__srv__FeatSetWorkMode_Response * rhs)
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
  return true;
}

bool
genie_msgs__srv__FeatSetWorkMode_Response__copy(
  const genie_msgs__srv__FeatSetWorkMode_Response * input,
  genie_msgs__srv__FeatSetWorkMode_Response * output)
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
  return true;
}

genie_msgs__srv__FeatSetWorkMode_Response *
genie_msgs__srv__FeatSetWorkMode_Response__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__srv__FeatSetWorkMode_Response * msg = (genie_msgs__srv__FeatSetWorkMode_Response *)allocator.allocate(sizeof(genie_msgs__srv__FeatSetWorkMode_Response), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(genie_msgs__srv__FeatSetWorkMode_Response));
  bool success = genie_msgs__srv__FeatSetWorkMode_Response__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
genie_msgs__srv__FeatSetWorkMode_Response__destroy(genie_msgs__srv__FeatSetWorkMode_Response * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    genie_msgs__srv__FeatSetWorkMode_Response__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
genie_msgs__srv__FeatSetWorkMode_Response__Sequence__init(genie_msgs__srv__FeatSetWorkMode_Response__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__srv__FeatSetWorkMode_Response * data = NULL;

  if (size) {
    data = (genie_msgs__srv__FeatSetWorkMode_Response *)allocator.zero_allocate(size, sizeof(genie_msgs__srv__FeatSetWorkMode_Response), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = genie_msgs__srv__FeatSetWorkMode_Response__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        genie_msgs__srv__FeatSetWorkMode_Response__fini(&data[i - 1]);
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
genie_msgs__srv__FeatSetWorkMode_Response__Sequence__fini(genie_msgs__srv__FeatSetWorkMode_Response__Sequence * array)
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
      genie_msgs__srv__FeatSetWorkMode_Response__fini(&array->data[i]);
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

genie_msgs__srv__FeatSetWorkMode_Response__Sequence *
genie_msgs__srv__FeatSetWorkMode_Response__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__srv__FeatSetWorkMode_Response__Sequence * array = (genie_msgs__srv__FeatSetWorkMode_Response__Sequence *)allocator.allocate(sizeof(genie_msgs__srv__FeatSetWorkMode_Response__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = genie_msgs__srv__FeatSetWorkMode_Response__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
genie_msgs__srv__FeatSetWorkMode_Response__Sequence__destroy(genie_msgs__srv__FeatSetWorkMode_Response__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    genie_msgs__srv__FeatSetWorkMode_Response__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
genie_msgs__srv__FeatSetWorkMode_Response__Sequence__are_equal(const genie_msgs__srv__FeatSetWorkMode_Response__Sequence * lhs, const genie_msgs__srv__FeatSetWorkMode_Response__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!genie_msgs__srv__FeatSetWorkMode_Response__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
genie_msgs__srv__FeatSetWorkMode_Response__Sequence__copy(
  const genie_msgs__srv__FeatSetWorkMode_Response__Sequence * input,
  genie_msgs__srv__FeatSetWorkMode_Response__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(genie_msgs__srv__FeatSetWorkMode_Response);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    genie_msgs__srv__FeatSetWorkMode_Response * data =
      (genie_msgs__srv__FeatSetWorkMode_Response *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!genie_msgs__srv__FeatSetWorkMode_Response__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          genie_msgs__srv__FeatSetWorkMode_Response__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!genie_msgs__srv__FeatSetWorkMode_Response__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
