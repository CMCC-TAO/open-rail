// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from genie_msgs:msg/Retarget.idl
// generated code does not contain a copyright notice
#include "genie_msgs/msg/detail/retarget__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"
// Member `left_ee_pose`
// Member `right_ee_pose`
// Member `left_upper_arm`
// Member `right_upper_arm`
#include "geometry_msgs/msg/detail/pose__functions.h"
// Member `body_joint_names`
#include "rosidl_runtime_c/string_functions.h"
// Member `body_joint_positions`
#include "rosidl_runtime_c/primitives_sequence_functions.h"

bool
genie_msgs__msg__Retarget__init(genie_msgs__msg__Retarget * msg)
{
  if (!msg) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__init(&msg->header)) {
    genie_msgs__msg__Retarget__fini(msg);
    return false;
  }
  // group_arms
  // group_body
  // device
  // left_ee_pose
  if (!geometry_msgs__msg__Pose__init(&msg->left_ee_pose)) {
    genie_msgs__msg__Retarget__fini(msg);
    return false;
  }
  // right_ee_pose
  if (!geometry_msgs__msg__Pose__init(&msg->right_ee_pose)) {
    genie_msgs__msg__Retarget__fini(msg);
    return false;
  }
  // left_upper_arm
  if (!geometry_msgs__msg__Pose__init(&msg->left_upper_arm)) {
    genie_msgs__msg__Retarget__fini(msg);
    return false;
  }
  // right_upper_arm
  if (!geometry_msgs__msg__Pose__init(&msg->right_upper_arm)) {
    genie_msgs__msg__Retarget__fini(msg);
    return false;
  }
  // body_joint_names
  if (!rosidl_runtime_c__String__Sequence__init(&msg->body_joint_names, 0)) {
    genie_msgs__msg__Retarget__fini(msg);
    return false;
  }
  // body_joint_positions
  if (!rosidl_runtime_c__double__Sequence__init(&msg->body_joint_positions, 0)) {
    genie_msgs__msg__Retarget__fini(msg);
    return false;
  }
  return true;
}

void
genie_msgs__msg__Retarget__fini(genie_msgs__msg__Retarget * msg)
{
  if (!msg) {
    return;
  }
  // header
  std_msgs__msg__Header__fini(&msg->header);
  // group_arms
  // group_body
  // device
  // left_ee_pose
  geometry_msgs__msg__Pose__fini(&msg->left_ee_pose);
  // right_ee_pose
  geometry_msgs__msg__Pose__fini(&msg->right_ee_pose);
  // left_upper_arm
  geometry_msgs__msg__Pose__fini(&msg->left_upper_arm);
  // right_upper_arm
  geometry_msgs__msg__Pose__fini(&msg->right_upper_arm);
  // body_joint_names
  rosidl_runtime_c__String__Sequence__fini(&msg->body_joint_names);
  // body_joint_positions
  rosidl_runtime_c__double__Sequence__fini(&msg->body_joint_positions);
}

bool
genie_msgs__msg__Retarget__are_equal(const genie_msgs__msg__Retarget * lhs, const genie_msgs__msg__Retarget * rhs)
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
  // group_arms
  if (lhs->group_arms != rhs->group_arms) {
    return false;
  }
  // group_body
  if (lhs->group_body != rhs->group_body) {
    return false;
  }
  // device
  if (lhs->device != rhs->device) {
    return false;
  }
  // left_ee_pose
  if (!geometry_msgs__msg__Pose__are_equal(
      &(lhs->left_ee_pose), &(rhs->left_ee_pose)))
  {
    return false;
  }
  // right_ee_pose
  if (!geometry_msgs__msg__Pose__are_equal(
      &(lhs->right_ee_pose), &(rhs->right_ee_pose)))
  {
    return false;
  }
  // left_upper_arm
  if (!geometry_msgs__msg__Pose__are_equal(
      &(lhs->left_upper_arm), &(rhs->left_upper_arm)))
  {
    return false;
  }
  // right_upper_arm
  if (!geometry_msgs__msg__Pose__are_equal(
      &(lhs->right_upper_arm), &(rhs->right_upper_arm)))
  {
    return false;
  }
  // body_joint_names
  if (!rosidl_runtime_c__String__Sequence__are_equal(
      &(lhs->body_joint_names), &(rhs->body_joint_names)))
  {
    return false;
  }
  // body_joint_positions
  if (!rosidl_runtime_c__double__Sequence__are_equal(
      &(lhs->body_joint_positions), &(rhs->body_joint_positions)))
  {
    return false;
  }
  return true;
}

bool
genie_msgs__msg__Retarget__copy(
  const genie_msgs__msg__Retarget * input,
  genie_msgs__msg__Retarget * output)
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
  // group_arms
  output->group_arms = input->group_arms;
  // group_body
  output->group_body = input->group_body;
  // device
  output->device = input->device;
  // left_ee_pose
  if (!geometry_msgs__msg__Pose__copy(
      &(input->left_ee_pose), &(output->left_ee_pose)))
  {
    return false;
  }
  // right_ee_pose
  if (!geometry_msgs__msg__Pose__copy(
      &(input->right_ee_pose), &(output->right_ee_pose)))
  {
    return false;
  }
  // left_upper_arm
  if (!geometry_msgs__msg__Pose__copy(
      &(input->left_upper_arm), &(output->left_upper_arm)))
  {
    return false;
  }
  // right_upper_arm
  if (!geometry_msgs__msg__Pose__copy(
      &(input->right_upper_arm), &(output->right_upper_arm)))
  {
    return false;
  }
  // body_joint_names
  if (!rosidl_runtime_c__String__Sequence__copy(
      &(input->body_joint_names), &(output->body_joint_names)))
  {
    return false;
  }
  // body_joint_positions
  if (!rosidl_runtime_c__double__Sequence__copy(
      &(input->body_joint_positions), &(output->body_joint_positions)))
  {
    return false;
  }
  return true;
}

genie_msgs__msg__Retarget *
genie_msgs__msg__Retarget__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__Retarget * msg = (genie_msgs__msg__Retarget *)allocator.allocate(sizeof(genie_msgs__msg__Retarget), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(genie_msgs__msg__Retarget));
  bool success = genie_msgs__msg__Retarget__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
genie_msgs__msg__Retarget__destroy(genie_msgs__msg__Retarget * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    genie_msgs__msg__Retarget__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
genie_msgs__msg__Retarget__Sequence__init(genie_msgs__msg__Retarget__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__Retarget * data = NULL;

  if (size) {
    data = (genie_msgs__msg__Retarget *)allocator.zero_allocate(size, sizeof(genie_msgs__msg__Retarget), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = genie_msgs__msg__Retarget__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        genie_msgs__msg__Retarget__fini(&data[i - 1]);
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
genie_msgs__msg__Retarget__Sequence__fini(genie_msgs__msg__Retarget__Sequence * array)
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
      genie_msgs__msg__Retarget__fini(&array->data[i]);
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

genie_msgs__msg__Retarget__Sequence *
genie_msgs__msg__Retarget__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__Retarget__Sequence * array = (genie_msgs__msg__Retarget__Sequence *)allocator.allocate(sizeof(genie_msgs__msg__Retarget__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = genie_msgs__msg__Retarget__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
genie_msgs__msg__Retarget__Sequence__destroy(genie_msgs__msg__Retarget__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    genie_msgs__msg__Retarget__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
genie_msgs__msg__Retarget__Sequence__are_equal(const genie_msgs__msg__Retarget__Sequence * lhs, const genie_msgs__msg__Retarget__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!genie_msgs__msg__Retarget__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
genie_msgs__msg__Retarget__Sequence__copy(
  const genie_msgs__msg__Retarget__Sequence * input,
  genie_msgs__msg__Retarget__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(genie_msgs__msg__Retarget);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    genie_msgs__msg__Retarget * data =
      (genie_msgs__msg__Retarget *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!genie_msgs__msg__Retarget__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          genie_msgs__msg__Retarget__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!genie_msgs__msg__Retarget__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
