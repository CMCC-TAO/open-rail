// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from genie_msgs:srv/NoitomSetFreq.idl
// generated code does not contain a copyright notice
#include "genie_msgs/srv/detail/noitom_set_freq__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"

bool
genie_msgs__srv__NoitomSetFreq_Request__init(genie_msgs__srv__NoitomSetFreq_Request * msg)
{
  if (!msg) {
    return false;
  }
  // frequency
  return true;
}

void
genie_msgs__srv__NoitomSetFreq_Request__fini(genie_msgs__srv__NoitomSetFreq_Request * msg)
{
  if (!msg) {
    return;
  }
  // frequency
}

bool
genie_msgs__srv__NoitomSetFreq_Request__are_equal(const genie_msgs__srv__NoitomSetFreq_Request * lhs, const genie_msgs__srv__NoitomSetFreq_Request * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // frequency
  if (lhs->frequency != rhs->frequency) {
    return false;
  }
  return true;
}

bool
genie_msgs__srv__NoitomSetFreq_Request__copy(
  const genie_msgs__srv__NoitomSetFreq_Request * input,
  genie_msgs__srv__NoitomSetFreq_Request * output)
{
  if (!input || !output) {
    return false;
  }
  // frequency
  output->frequency = input->frequency;
  return true;
}

genie_msgs__srv__NoitomSetFreq_Request *
genie_msgs__srv__NoitomSetFreq_Request__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__srv__NoitomSetFreq_Request * msg = (genie_msgs__srv__NoitomSetFreq_Request *)allocator.allocate(sizeof(genie_msgs__srv__NoitomSetFreq_Request), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(genie_msgs__srv__NoitomSetFreq_Request));
  bool success = genie_msgs__srv__NoitomSetFreq_Request__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
genie_msgs__srv__NoitomSetFreq_Request__destroy(genie_msgs__srv__NoitomSetFreq_Request * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    genie_msgs__srv__NoitomSetFreq_Request__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
genie_msgs__srv__NoitomSetFreq_Request__Sequence__init(genie_msgs__srv__NoitomSetFreq_Request__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__srv__NoitomSetFreq_Request * data = NULL;

  if (size) {
    data = (genie_msgs__srv__NoitomSetFreq_Request *)allocator.zero_allocate(size, sizeof(genie_msgs__srv__NoitomSetFreq_Request), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = genie_msgs__srv__NoitomSetFreq_Request__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        genie_msgs__srv__NoitomSetFreq_Request__fini(&data[i - 1]);
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
genie_msgs__srv__NoitomSetFreq_Request__Sequence__fini(genie_msgs__srv__NoitomSetFreq_Request__Sequence * array)
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
      genie_msgs__srv__NoitomSetFreq_Request__fini(&array->data[i]);
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

genie_msgs__srv__NoitomSetFreq_Request__Sequence *
genie_msgs__srv__NoitomSetFreq_Request__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__srv__NoitomSetFreq_Request__Sequence * array = (genie_msgs__srv__NoitomSetFreq_Request__Sequence *)allocator.allocate(sizeof(genie_msgs__srv__NoitomSetFreq_Request__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = genie_msgs__srv__NoitomSetFreq_Request__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
genie_msgs__srv__NoitomSetFreq_Request__Sequence__destroy(genie_msgs__srv__NoitomSetFreq_Request__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    genie_msgs__srv__NoitomSetFreq_Request__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
genie_msgs__srv__NoitomSetFreq_Request__Sequence__are_equal(const genie_msgs__srv__NoitomSetFreq_Request__Sequence * lhs, const genie_msgs__srv__NoitomSetFreq_Request__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!genie_msgs__srv__NoitomSetFreq_Request__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
genie_msgs__srv__NoitomSetFreq_Request__Sequence__copy(
  const genie_msgs__srv__NoitomSetFreq_Request__Sequence * input,
  genie_msgs__srv__NoitomSetFreq_Request__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(genie_msgs__srv__NoitomSetFreq_Request);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    genie_msgs__srv__NoitomSetFreq_Request * data =
      (genie_msgs__srv__NoitomSetFreq_Request *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!genie_msgs__srv__NoitomSetFreq_Request__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          genie_msgs__srv__NoitomSetFreq_Request__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!genie_msgs__srv__NoitomSetFreq_Request__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `message`
#include "rosidl_runtime_c/string_functions.h"

bool
genie_msgs__srv__NoitomSetFreq_Response__init(genie_msgs__srv__NoitomSetFreq_Response * msg)
{
  if (!msg) {
    return false;
  }
  // success
  // current_frequency
  // message
  if (!rosidl_runtime_c__String__init(&msg->message)) {
    genie_msgs__srv__NoitomSetFreq_Response__fini(msg);
    return false;
  }
  return true;
}

void
genie_msgs__srv__NoitomSetFreq_Response__fini(genie_msgs__srv__NoitomSetFreq_Response * msg)
{
  if (!msg) {
    return;
  }
  // success
  // current_frequency
  // message
  rosidl_runtime_c__String__fini(&msg->message);
}

bool
genie_msgs__srv__NoitomSetFreq_Response__are_equal(const genie_msgs__srv__NoitomSetFreq_Response * lhs, const genie_msgs__srv__NoitomSetFreq_Response * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // success
  if (lhs->success != rhs->success) {
    return false;
  }
  // current_frequency
  if (lhs->current_frequency != rhs->current_frequency) {
    return false;
  }
  // message
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->message), &(rhs->message)))
  {
    return false;
  }
  return true;
}

bool
genie_msgs__srv__NoitomSetFreq_Response__copy(
  const genie_msgs__srv__NoitomSetFreq_Response * input,
  genie_msgs__srv__NoitomSetFreq_Response * output)
{
  if (!input || !output) {
    return false;
  }
  // success
  output->success = input->success;
  // current_frequency
  output->current_frequency = input->current_frequency;
  // message
  if (!rosidl_runtime_c__String__copy(
      &(input->message), &(output->message)))
  {
    return false;
  }
  return true;
}

genie_msgs__srv__NoitomSetFreq_Response *
genie_msgs__srv__NoitomSetFreq_Response__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__srv__NoitomSetFreq_Response * msg = (genie_msgs__srv__NoitomSetFreq_Response *)allocator.allocate(sizeof(genie_msgs__srv__NoitomSetFreq_Response), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(genie_msgs__srv__NoitomSetFreq_Response));
  bool success = genie_msgs__srv__NoitomSetFreq_Response__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
genie_msgs__srv__NoitomSetFreq_Response__destroy(genie_msgs__srv__NoitomSetFreq_Response * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    genie_msgs__srv__NoitomSetFreq_Response__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
genie_msgs__srv__NoitomSetFreq_Response__Sequence__init(genie_msgs__srv__NoitomSetFreq_Response__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__srv__NoitomSetFreq_Response * data = NULL;

  if (size) {
    data = (genie_msgs__srv__NoitomSetFreq_Response *)allocator.zero_allocate(size, sizeof(genie_msgs__srv__NoitomSetFreq_Response), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = genie_msgs__srv__NoitomSetFreq_Response__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        genie_msgs__srv__NoitomSetFreq_Response__fini(&data[i - 1]);
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
genie_msgs__srv__NoitomSetFreq_Response__Sequence__fini(genie_msgs__srv__NoitomSetFreq_Response__Sequence * array)
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
      genie_msgs__srv__NoitomSetFreq_Response__fini(&array->data[i]);
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

genie_msgs__srv__NoitomSetFreq_Response__Sequence *
genie_msgs__srv__NoitomSetFreq_Response__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__srv__NoitomSetFreq_Response__Sequence * array = (genie_msgs__srv__NoitomSetFreq_Response__Sequence *)allocator.allocate(sizeof(genie_msgs__srv__NoitomSetFreq_Response__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = genie_msgs__srv__NoitomSetFreq_Response__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
genie_msgs__srv__NoitomSetFreq_Response__Sequence__destroy(genie_msgs__srv__NoitomSetFreq_Response__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    genie_msgs__srv__NoitomSetFreq_Response__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
genie_msgs__srv__NoitomSetFreq_Response__Sequence__are_equal(const genie_msgs__srv__NoitomSetFreq_Response__Sequence * lhs, const genie_msgs__srv__NoitomSetFreq_Response__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!genie_msgs__srv__NoitomSetFreq_Response__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
genie_msgs__srv__NoitomSetFreq_Response__Sequence__copy(
  const genie_msgs__srv__NoitomSetFreq_Response__Sequence * input,
  genie_msgs__srv__NoitomSetFreq_Response__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(genie_msgs__srv__NoitomSetFreq_Response);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    genie_msgs__srv__NoitomSetFreq_Response * data =
      (genie_msgs__srv__NoitomSetFreq_Response *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!genie_msgs__srv__NoitomSetFreq_Response__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          genie_msgs__srv__NoitomSetFreq_Response__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!genie_msgs__srv__NoitomSetFreq_Response__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
