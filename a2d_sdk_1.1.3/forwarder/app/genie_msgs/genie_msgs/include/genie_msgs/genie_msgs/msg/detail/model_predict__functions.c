// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from genie_msgs:msg/ModelPredict.idl
// generated code does not contain a copyright notice
#include "genie_msgs/msg/detail/model_predict__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"
// Member `body_joint_names`
#include "rosidl_runtime_c/string_functions.h"
// Member `body_joint_positions`
#include "rosidl_runtime_c/primitives_sequence_functions.h"
// Member `target_poses`
#include "geometry_msgs/msg/detail/pose__functions.h"
// Member `target_joint_states`
#include "sensor_msgs/msg/detail/joint_state__functions.h"

bool
genie_msgs__msg__ModelPredict__init(genie_msgs__msg__ModelPredict * msg)
{
  if (!msg) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__init(&msg->header)) {
    genie_msgs__msg__ModelPredict__fini(msg);
    return false;
  }
  // body_joint_names
  if (!rosidl_runtime_c__String__Sequence__init(&msg->body_joint_names, 0)) {
    genie_msgs__msg__ModelPredict__fini(msg);
    return false;
  }
  // body_joint_positions
  if (!rosidl_runtime_c__double__Sequence__init(&msg->body_joint_positions, 0)) {
    genie_msgs__msg__ModelPredict__fini(msg);
    return false;
  }
  // model_output_type
  // target_poses
  if (!geometry_msgs__msg__Pose__Sequence__init(&msg->target_poses, 0)) {
    genie_msgs__msg__ModelPredict__fini(msg);
    return false;
  }
  // target_joint_states
  if (!sensor_msgs__msg__JointState__Sequence__init(&msg->target_joint_states, 0)) {
    genie_msgs__msg__ModelPredict__fini(msg);
    return false;
  }
  // model_sleep_time
  // trajectory_reference_time
  return true;
}

void
genie_msgs__msg__ModelPredict__fini(genie_msgs__msg__ModelPredict * msg)
{
  if (!msg) {
    return;
  }
  // header
  std_msgs__msg__Header__fini(&msg->header);
  // body_joint_names
  rosidl_runtime_c__String__Sequence__fini(&msg->body_joint_names);
  // body_joint_positions
  rosidl_runtime_c__double__Sequence__fini(&msg->body_joint_positions);
  // model_output_type
  // target_poses
  geometry_msgs__msg__Pose__Sequence__fini(&msg->target_poses);
  // target_joint_states
  sensor_msgs__msg__JointState__Sequence__fini(&msg->target_joint_states);
  // model_sleep_time
  // trajectory_reference_time
}

bool
genie_msgs__msg__ModelPredict__are_equal(const genie_msgs__msg__ModelPredict * lhs, const genie_msgs__msg__ModelPredict * rhs)
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
  // model_output_type
  if (lhs->model_output_type != rhs->model_output_type) {
    return false;
  }
  // target_poses
  if (!geometry_msgs__msg__Pose__Sequence__are_equal(
      &(lhs->target_poses), &(rhs->target_poses)))
  {
    return false;
  }
  // target_joint_states
  if (!sensor_msgs__msg__JointState__Sequence__are_equal(
      &(lhs->target_joint_states), &(rhs->target_joint_states)))
  {
    return false;
  }
  // model_sleep_time
  if (lhs->model_sleep_time != rhs->model_sleep_time) {
    return false;
  }
  // trajectory_reference_time
  if (lhs->trajectory_reference_time != rhs->trajectory_reference_time) {
    return false;
  }
  return true;
}

bool
genie_msgs__msg__ModelPredict__copy(
  const genie_msgs__msg__ModelPredict * input,
  genie_msgs__msg__ModelPredict * output)
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
  // model_output_type
  output->model_output_type = input->model_output_type;
  // target_poses
  if (!geometry_msgs__msg__Pose__Sequence__copy(
      &(input->target_poses), &(output->target_poses)))
  {
    return false;
  }
  // target_joint_states
  if (!sensor_msgs__msg__JointState__Sequence__copy(
      &(input->target_joint_states), &(output->target_joint_states)))
  {
    return false;
  }
  // model_sleep_time
  output->model_sleep_time = input->model_sleep_time;
  // trajectory_reference_time
  output->trajectory_reference_time = input->trajectory_reference_time;
  return true;
}

genie_msgs__msg__ModelPredict *
genie_msgs__msg__ModelPredict__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__ModelPredict * msg = (genie_msgs__msg__ModelPredict *)allocator.allocate(sizeof(genie_msgs__msg__ModelPredict), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(genie_msgs__msg__ModelPredict));
  bool success = genie_msgs__msg__ModelPredict__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
genie_msgs__msg__ModelPredict__destroy(genie_msgs__msg__ModelPredict * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    genie_msgs__msg__ModelPredict__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
genie_msgs__msg__ModelPredict__Sequence__init(genie_msgs__msg__ModelPredict__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__ModelPredict * data = NULL;

  if (size) {
    data = (genie_msgs__msg__ModelPredict *)allocator.zero_allocate(size, sizeof(genie_msgs__msg__ModelPredict), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = genie_msgs__msg__ModelPredict__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        genie_msgs__msg__ModelPredict__fini(&data[i - 1]);
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
genie_msgs__msg__ModelPredict__Sequence__fini(genie_msgs__msg__ModelPredict__Sequence * array)
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
      genie_msgs__msg__ModelPredict__fini(&array->data[i]);
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

genie_msgs__msg__ModelPredict__Sequence *
genie_msgs__msg__ModelPredict__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__ModelPredict__Sequence * array = (genie_msgs__msg__ModelPredict__Sequence *)allocator.allocate(sizeof(genie_msgs__msg__ModelPredict__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = genie_msgs__msg__ModelPredict__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
genie_msgs__msg__ModelPredict__Sequence__destroy(genie_msgs__msg__ModelPredict__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    genie_msgs__msg__ModelPredict__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
genie_msgs__msg__ModelPredict__Sequence__are_equal(const genie_msgs__msg__ModelPredict__Sequence * lhs, const genie_msgs__msg__ModelPredict__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!genie_msgs__msg__ModelPredict__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
genie_msgs__msg__ModelPredict__Sequence__copy(
  const genie_msgs__msg__ModelPredict__Sequence * input,
  genie_msgs__msg__ModelPredict__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(genie_msgs__msg__ModelPredict);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    genie_msgs__msg__ModelPredict * data =
      (genie_msgs__msg__ModelPredict *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!genie_msgs__msg__ModelPredict__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          genie_msgs__msg__ModelPredict__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!genie_msgs__msg__ModelPredict__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
