// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from genie_msgs:msg/WholeBodyStatus.idl
// generated code does not contain a copyright notice
#include "genie_msgs/msg/detail/whole_body_status__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"

bool
genie_msgs__msg__WholeBodyStatus__init(genie_msgs__msg__WholeBodyStatus * msg)
{
  if (!msg) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__init(&msg->header)) {
    genie_msgs__msg__WholeBodyStatus__fini(msg);
    return false;
  }
  // right_arm_error
  // left_arm_error
  // right_arm_control
  // left_arm_control
  // right_arm_estop
  // left_arm_estop
  // right_end_error
  // left_end_error
  // waist_error
  // lift_error
  // neck_error
  // chassis_error
  return true;
}

void
genie_msgs__msg__WholeBodyStatus__fini(genie_msgs__msg__WholeBodyStatus * msg)
{
  if (!msg) {
    return;
  }
  // header
  std_msgs__msg__Header__fini(&msg->header);
  // right_arm_error
  // left_arm_error
  // right_arm_control
  // left_arm_control
  // right_arm_estop
  // left_arm_estop
  // right_end_error
  // left_end_error
  // waist_error
  // lift_error
  // neck_error
  // chassis_error
}

bool
genie_msgs__msg__WholeBodyStatus__are_equal(const genie_msgs__msg__WholeBodyStatus * lhs, const genie_msgs__msg__WholeBodyStatus * rhs)
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
  // right_arm_error
  if (lhs->right_arm_error != rhs->right_arm_error) {
    return false;
  }
  // left_arm_error
  if (lhs->left_arm_error != rhs->left_arm_error) {
    return false;
  }
  // right_arm_control
  if (lhs->right_arm_control != rhs->right_arm_control) {
    return false;
  }
  // left_arm_control
  if (lhs->left_arm_control != rhs->left_arm_control) {
    return false;
  }
  // right_arm_estop
  if (lhs->right_arm_estop != rhs->right_arm_estop) {
    return false;
  }
  // left_arm_estop
  if (lhs->left_arm_estop != rhs->left_arm_estop) {
    return false;
  }
  // right_end_error
  if (lhs->right_end_error != rhs->right_end_error) {
    return false;
  }
  // left_end_error
  if (lhs->left_end_error != rhs->left_end_error) {
    return false;
  }
  // waist_error
  if (lhs->waist_error != rhs->waist_error) {
    return false;
  }
  // lift_error
  if (lhs->lift_error != rhs->lift_error) {
    return false;
  }
  // neck_error
  if (lhs->neck_error != rhs->neck_error) {
    return false;
  }
  // chassis_error
  if (lhs->chassis_error != rhs->chassis_error) {
    return false;
  }
  return true;
}

bool
genie_msgs__msg__WholeBodyStatus__copy(
  const genie_msgs__msg__WholeBodyStatus * input,
  genie_msgs__msg__WholeBodyStatus * output)
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
  // right_arm_error
  output->right_arm_error = input->right_arm_error;
  // left_arm_error
  output->left_arm_error = input->left_arm_error;
  // right_arm_control
  output->right_arm_control = input->right_arm_control;
  // left_arm_control
  output->left_arm_control = input->left_arm_control;
  // right_arm_estop
  output->right_arm_estop = input->right_arm_estop;
  // left_arm_estop
  output->left_arm_estop = input->left_arm_estop;
  // right_end_error
  output->right_end_error = input->right_end_error;
  // left_end_error
  output->left_end_error = input->left_end_error;
  // waist_error
  output->waist_error = input->waist_error;
  // lift_error
  output->lift_error = input->lift_error;
  // neck_error
  output->neck_error = input->neck_error;
  // chassis_error
  output->chassis_error = input->chassis_error;
  return true;
}

genie_msgs__msg__WholeBodyStatus *
genie_msgs__msg__WholeBodyStatus__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__WholeBodyStatus * msg = (genie_msgs__msg__WholeBodyStatus *)allocator.allocate(sizeof(genie_msgs__msg__WholeBodyStatus), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(genie_msgs__msg__WholeBodyStatus));
  bool success = genie_msgs__msg__WholeBodyStatus__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
genie_msgs__msg__WholeBodyStatus__destroy(genie_msgs__msg__WholeBodyStatus * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    genie_msgs__msg__WholeBodyStatus__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
genie_msgs__msg__WholeBodyStatus__Sequence__init(genie_msgs__msg__WholeBodyStatus__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__WholeBodyStatus * data = NULL;

  if (size) {
    data = (genie_msgs__msg__WholeBodyStatus *)allocator.zero_allocate(size, sizeof(genie_msgs__msg__WholeBodyStatus), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = genie_msgs__msg__WholeBodyStatus__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        genie_msgs__msg__WholeBodyStatus__fini(&data[i - 1]);
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
genie_msgs__msg__WholeBodyStatus__Sequence__fini(genie_msgs__msg__WholeBodyStatus__Sequence * array)
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
      genie_msgs__msg__WholeBodyStatus__fini(&array->data[i]);
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

genie_msgs__msg__WholeBodyStatus__Sequence *
genie_msgs__msg__WholeBodyStatus__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__WholeBodyStatus__Sequence * array = (genie_msgs__msg__WholeBodyStatus__Sequence *)allocator.allocate(sizeof(genie_msgs__msg__WholeBodyStatus__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = genie_msgs__msg__WholeBodyStatus__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
genie_msgs__msg__WholeBodyStatus__Sequence__destroy(genie_msgs__msg__WholeBodyStatus__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    genie_msgs__msg__WholeBodyStatus__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
genie_msgs__msg__WholeBodyStatus__Sequence__are_equal(const genie_msgs__msg__WholeBodyStatus__Sequence * lhs, const genie_msgs__msg__WholeBodyStatus__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!genie_msgs__msg__WholeBodyStatus__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
genie_msgs__msg__WholeBodyStatus__Sequence__copy(
  const genie_msgs__msg__WholeBodyStatus__Sequence * input,
  genie_msgs__msg__WholeBodyStatus__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(genie_msgs__msg__WholeBodyStatus);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    genie_msgs__msg__WholeBodyStatus * data =
      (genie_msgs__msg__WholeBodyStatus *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!genie_msgs__msg__WholeBodyStatus__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          genie_msgs__msg__WholeBodyStatus__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!genie_msgs__msg__WholeBodyStatus__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
