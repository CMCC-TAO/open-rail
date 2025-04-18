// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from genie_msgs:msg/FimFirmware.idl
// generated code does not contain a copyright notice
#include "genie_msgs/msg/detail/fim_firmware__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"

bool
genie_msgs__msg__FimFirmware__init(genie_msgs__msg__FimFirmware * msg)
{
  if (!msg) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__init(&msg->header)) {
    genie_msgs__msg__FimFirmware__fini(msg);
    return false;
  }
  // fim_fw
  // err_code_byte
  return true;
}

void
genie_msgs__msg__FimFirmware__fini(genie_msgs__msg__FimFirmware * msg)
{
  if (!msg) {
    return;
  }
  // header
  std_msgs__msg__Header__fini(&msg->header);
  // fim_fw
  // err_code_byte
}

bool
genie_msgs__msg__FimFirmware__are_equal(const genie_msgs__msg__FimFirmware * lhs, const genie_msgs__msg__FimFirmware * rhs)
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
  // fim_fw
  if (lhs->fim_fw != rhs->fim_fw) {
    return false;
  }
  // err_code_byte
  if (lhs->err_code_byte != rhs->err_code_byte) {
    return false;
  }
  return true;
}

bool
genie_msgs__msg__FimFirmware__copy(
  const genie_msgs__msg__FimFirmware * input,
  genie_msgs__msg__FimFirmware * output)
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
  // fim_fw
  output->fim_fw = input->fim_fw;
  // err_code_byte
  output->err_code_byte = input->err_code_byte;
  return true;
}

genie_msgs__msg__FimFirmware *
genie_msgs__msg__FimFirmware__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__FimFirmware * msg = (genie_msgs__msg__FimFirmware *)allocator.allocate(sizeof(genie_msgs__msg__FimFirmware), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(genie_msgs__msg__FimFirmware));
  bool success = genie_msgs__msg__FimFirmware__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
genie_msgs__msg__FimFirmware__destroy(genie_msgs__msg__FimFirmware * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    genie_msgs__msg__FimFirmware__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
genie_msgs__msg__FimFirmware__Sequence__init(genie_msgs__msg__FimFirmware__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__FimFirmware * data = NULL;

  if (size) {
    data = (genie_msgs__msg__FimFirmware *)allocator.zero_allocate(size, sizeof(genie_msgs__msg__FimFirmware), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = genie_msgs__msg__FimFirmware__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        genie_msgs__msg__FimFirmware__fini(&data[i - 1]);
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
genie_msgs__msg__FimFirmware__Sequence__fini(genie_msgs__msg__FimFirmware__Sequence * array)
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
      genie_msgs__msg__FimFirmware__fini(&array->data[i]);
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

genie_msgs__msg__FimFirmware__Sequence *
genie_msgs__msg__FimFirmware__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__FimFirmware__Sequence * array = (genie_msgs__msg__FimFirmware__Sequence *)allocator.allocate(sizeof(genie_msgs__msg__FimFirmware__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = genie_msgs__msg__FimFirmware__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
genie_msgs__msg__FimFirmware__Sequence__destroy(genie_msgs__msg__FimFirmware__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    genie_msgs__msg__FimFirmware__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
genie_msgs__msg__FimFirmware__Sequence__are_equal(const genie_msgs__msg__FimFirmware__Sequence * lhs, const genie_msgs__msg__FimFirmware__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!genie_msgs__msg__FimFirmware__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
genie_msgs__msg__FimFirmware__Sequence__copy(
  const genie_msgs__msg__FimFirmware__Sequence * input,
  genie_msgs__msg__FimFirmware__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(genie_msgs__msg__FimFirmware);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    genie_msgs__msg__FimFirmware * data =
      (genie_msgs__msg__FimFirmware *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!genie_msgs__msg__FimFirmware__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          genie_msgs__msg__FimFirmware__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!genie_msgs__msg__FimFirmware__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
