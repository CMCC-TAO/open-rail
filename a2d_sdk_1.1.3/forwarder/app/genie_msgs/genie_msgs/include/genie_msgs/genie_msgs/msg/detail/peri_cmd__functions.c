// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from genie_msgs:msg/PeriCmd.idl
// generated code does not contain a copyright notice
#include "genie_msgs/msg/detail/peri_cmd__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"

bool
genie_msgs__msg__PeriCmd__init(genie_msgs__msg__PeriCmd * msg)
{
  if (!msg) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__init(&msg->header)) {
    genie_msgs__msg__PeriCmd__fini(msg);
    return false;
  }
  // compute_center_ready_shut_down
  // soft_emergency_stop
  // hub1_reset_request
  // hub2_reset_request
  // left_arm_reset_request
  // right_arm_reset_request
  // left_end_reset_request
  // right_end_reset_request
  // waist_pitch_motor_reset_request
  // lift_motor_reset_request
  // head_yaw_motor_reset_request
  // head_pitch_motor_reset_request
  // agv_reset_request
  // work_mode
  // feature_status
  // left_arm_power_ctrl_req
  // right_arm_power_ctrl_req
  // left_end_power_ctrl_req
  // right_end_power_ctrl_req
  // waist_pitch_motor_power_ctrl_req
  // lift_motor_power_ctrl_req
  // head_yaw_motor_power_ctrl_req
  // head_pitch_motor_power_ctrl_req
  // agv_power_ctrl_req
  return true;
}

void
genie_msgs__msg__PeriCmd__fini(genie_msgs__msg__PeriCmd * msg)
{
  if (!msg) {
    return;
  }
  // header
  std_msgs__msg__Header__fini(&msg->header);
  // compute_center_ready_shut_down
  // soft_emergency_stop
  // hub1_reset_request
  // hub2_reset_request
  // left_arm_reset_request
  // right_arm_reset_request
  // left_end_reset_request
  // right_end_reset_request
  // waist_pitch_motor_reset_request
  // lift_motor_reset_request
  // head_yaw_motor_reset_request
  // head_pitch_motor_reset_request
  // agv_reset_request
  // work_mode
  // feature_status
  // left_arm_power_ctrl_req
  // right_arm_power_ctrl_req
  // left_end_power_ctrl_req
  // right_end_power_ctrl_req
  // waist_pitch_motor_power_ctrl_req
  // lift_motor_power_ctrl_req
  // head_yaw_motor_power_ctrl_req
  // head_pitch_motor_power_ctrl_req
  // agv_power_ctrl_req
}

bool
genie_msgs__msg__PeriCmd__are_equal(const genie_msgs__msg__PeriCmd * lhs, const genie_msgs__msg__PeriCmd * rhs)
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
  // compute_center_ready_shut_down
  if (lhs->compute_center_ready_shut_down != rhs->compute_center_ready_shut_down) {
    return false;
  }
  // soft_emergency_stop
  if (lhs->soft_emergency_stop != rhs->soft_emergency_stop) {
    return false;
  }
  // hub1_reset_request
  if (lhs->hub1_reset_request != rhs->hub1_reset_request) {
    return false;
  }
  // hub2_reset_request
  if (lhs->hub2_reset_request != rhs->hub2_reset_request) {
    return false;
  }
  // left_arm_reset_request
  if (lhs->left_arm_reset_request != rhs->left_arm_reset_request) {
    return false;
  }
  // right_arm_reset_request
  if (lhs->right_arm_reset_request != rhs->right_arm_reset_request) {
    return false;
  }
  // left_end_reset_request
  if (lhs->left_end_reset_request != rhs->left_end_reset_request) {
    return false;
  }
  // right_end_reset_request
  if (lhs->right_end_reset_request != rhs->right_end_reset_request) {
    return false;
  }
  // waist_pitch_motor_reset_request
  if (lhs->waist_pitch_motor_reset_request != rhs->waist_pitch_motor_reset_request) {
    return false;
  }
  // lift_motor_reset_request
  if (lhs->lift_motor_reset_request != rhs->lift_motor_reset_request) {
    return false;
  }
  // head_yaw_motor_reset_request
  if (lhs->head_yaw_motor_reset_request != rhs->head_yaw_motor_reset_request) {
    return false;
  }
  // head_pitch_motor_reset_request
  if (lhs->head_pitch_motor_reset_request != rhs->head_pitch_motor_reset_request) {
    return false;
  }
  // agv_reset_request
  if (lhs->agv_reset_request != rhs->agv_reset_request) {
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
  // left_arm_power_ctrl_req
  if (lhs->left_arm_power_ctrl_req != rhs->left_arm_power_ctrl_req) {
    return false;
  }
  // right_arm_power_ctrl_req
  if (lhs->right_arm_power_ctrl_req != rhs->right_arm_power_ctrl_req) {
    return false;
  }
  // left_end_power_ctrl_req
  if (lhs->left_end_power_ctrl_req != rhs->left_end_power_ctrl_req) {
    return false;
  }
  // right_end_power_ctrl_req
  if (lhs->right_end_power_ctrl_req != rhs->right_end_power_ctrl_req) {
    return false;
  }
  // waist_pitch_motor_power_ctrl_req
  if (lhs->waist_pitch_motor_power_ctrl_req != rhs->waist_pitch_motor_power_ctrl_req) {
    return false;
  }
  // lift_motor_power_ctrl_req
  if (lhs->lift_motor_power_ctrl_req != rhs->lift_motor_power_ctrl_req) {
    return false;
  }
  // head_yaw_motor_power_ctrl_req
  if (lhs->head_yaw_motor_power_ctrl_req != rhs->head_yaw_motor_power_ctrl_req) {
    return false;
  }
  // head_pitch_motor_power_ctrl_req
  if (lhs->head_pitch_motor_power_ctrl_req != rhs->head_pitch_motor_power_ctrl_req) {
    return false;
  }
  // agv_power_ctrl_req
  if (lhs->agv_power_ctrl_req != rhs->agv_power_ctrl_req) {
    return false;
  }
  return true;
}

bool
genie_msgs__msg__PeriCmd__copy(
  const genie_msgs__msg__PeriCmd * input,
  genie_msgs__msg__PeriCmd * output)
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
  // compute_center_ready_shut_down
  output->compute_center_ready_shut_down = input->compute_center_ready_shut_down;
  // soft_emergency_stop
  output->soft_emergency_stop = input->soft_emergency_stop;
  // hub1_reset_request
  output->hub1_reset_request = input->hub1_reset_request;
  // hub2_reset_request
  output->hub2_reset_request = input->hub2_reset_request;
  // left_arm_reset_request
  output->left_arm_reset_request = input->left_arm_reset_request;
  // right_arm_reset_request
  output->right_arm_reset_request = input->right_arm_reset_request;
  // left_end_reset_request
  output->left_end_reset_request = input->left_end_reset_request;
  // right_end_reset_request
  output->right_end_reset_request = input->right_end_reset_request;
  // waist_pitch_motor_reset_request
  output->waist_pitch_motor_reset_request = input->waist_pitch_motor_reset_request;
  // lift_motor_reset_request
  output->lift_motor_reset_request = input->lift_motor_reset_request;
  // head_yaw_motor_reset_request
  output->head_yaw_motor_reset_request = input->head_yaw_motor_reset_request;
  // head_pitch_motor_reset_request
  output->head_pitch_motor_reset_request = input->head_pitch_motor_reset_request;
  // agv_reset_request
  output->agv_reset_request = input->agv_reset_request;
  // work_mode
  output->work_mode = input->work_mode;
  // feature_status
  output->feature_status = input->feature_status;
  // left_arm_power_ctrl_req
  output->left_arm_power_ctrl_req = input->left_arm_power_ctrl_req;
  // right_arm_power_ctrl_req
  output->right_arm_power_ctrl_req = input->right_arm_power_ctrl_req;
  // left_end_power_ctrl_req
  output->left_end_power_ctrl_req = input->left_end_power_ctrl_req;
  // right_end_power_ctrl_req
  output->right_end_power_ctrl_req = input->right_end_power_ctrl_req;
  // waist_pitch_motor_power_ctrl_req
  output->waist_pitch_motor_power_ctrl_req = input->waist_pitch_motor_power_ctrl_req;
  // lift_motor_power_ctrl_req
  output->lift_motor_power_ctrl_req = input->lift_motor_power_ctrl_req;
  // head_yaw_motor_power_ctrl_req
  output->head_yaw_motor_power_ctrl_req = input->head_yaw_motor_power_ctrl_req;
  // head_pitch_motor_power_ctrl_req
  output->head_pitch_motor_power_ctrl_req = input->head_pitch_motor_power_ctrl_req;
  // agv_power_ctrl_req
  output->agv_power_ctrl_req = input->agv_power_ctrl_req;
  return true;
}

genie_msgs__msg__PeriCmd *
genie_msgs__msg__PeriCmd__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__PeriCmd * msg = (genie_msgs__msg__PeriCmd *)allocator.allocate(sizeof(genie_msgs__msg__PeriCmd), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(genie_msgs__msg__PeriCmd));
  bool success = genie_msgs__msg__PeriCmd__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
genie_msgs__msg__PeriCmd__destroy(genie_msgs__msg__PeriCmd * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    genie_msgs__msg__PeriCmd__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
genie_msgs__msg__PeriCmd__Sequence__init(genie_msgs__msg__PeriCmd__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__PeriCmd * data = NULL;

  if (size) {
    data = (genie_msgs__msg__PeriCmd *)allocator.zero_allocate(size, sizeof(genie_msgs__msg__PeriCmd), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = genie_msgs__msg__PeriCmd__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        genie_msgs__msg__PeriCmd__fini(&data[i - 1]);
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
genie_msgs__msg__PeriCmd__Sequence__fini(genie_msgs__msg__PeriCmd__Sequence * array)
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
      genie_msgs__msg__PeriCmd__fini(&array->data[i]);
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

genie_msgs__msg__PeriCmd__Sequence *
genie_msgs__msg__PeriCmd__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__PeriCmd__Sequence * array = (genie_msgs__msg__PeriCmd__Sequence *)allocator.allocate(sizeof(genie_msgs__msg__PeriCmd__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = genie_msgs__msg__PeriCmd__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
genie_msgs__msg__PeriCmd__Sequence__destroy(genie_msgs__msg__PeriCmd__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    genie_msgs__msg__PeriCmd__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
genie_msgs__msg__PeriCmd__Sequence__are_equal(const genie_msgs__msg__PeriCmd__Sequence * lhs, const genie_msgs__msg__PeriCmd__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!genie_msgs__msg__PeriCmd__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
genie_msgs__msg__PeriCmd__Sequence__copy(
  const genie_msgs__msg__PeriCmd__Sequence * input,
  genie_msgs__msg__PeriCmd__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(genie_msgs__msg__PeriCmd);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    genie_msgs__msg__PeriCmd * data =
      (genie_msgs__msg__PeriCmd *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!genie_msgs__msg__PeriCmd__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          genie_msgs__msg__PeriCmd__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!genie_msgs__msg__PeriCmd__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
