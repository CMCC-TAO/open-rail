// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from genie_msgs:msg/PeriStatus.idl
// generated code does not contain a copyright notice
#include "genie_msgs/msg/detail/peri_status__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"
// Member `power_board_software_version`
// Member `power_board_hardware_version`
// Member `power_board_serial_number`
#include "rosidl_runtime_c/string_functions.h"

bool
genie_msgs__msg__PeriStatus__init(genie_msgs__msg__PeriStatus * msg)
{
  if (!msg) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__init(&msg->header)) {
    genie_msgs__msg__PeriStatus__fini(msg);
    return false;
  }
  // shut_down_compute_center_request
  // soft_emergency_stop_feedback
  // pedal_emergency_stop
  // button_emergency_stop
  // hub1_reset_request_feedback
  // hub2_reset_request_feedback
  // left_arm_reset_request_feedback
  // right_arm_reset_request_feedback
  // left_end_reset_request_feedback
  // right_end_reset_request_feedback
  // waist_pitch_motor_reset_request_feedback
  // lift_motor_reset_request_feedback
  // head_yaw_motor_reset_request_feedback
  // head_pitch_motor_reset_request_feedback
  // agv_reset_request_feedback
  // power_pcb_work_mode
  // feature_status
  // left_arm_power_ctrl_req_feedback
  // right_arm_power_ctrl_req_feedback
  // left_end_power_ctrl_req_feedback
  // right_end_power_ctrl_req_feedback
  // waist_pitch_motor_power_ctrl_req_feedback
  // lift_motor_power_ctrl_req_feedback
  // head_yaw_motor_power_ctrl_req_feedback
  // head_pitch_motor_power_ctrl_req_feedback
  // agv_power_ctrl_req_feedback
  // power_ctrl_req_failreason
  // left_end_current
  // right_end_current
  // waist_pitch_motor_current
  // lift_motor_current
  // head_yaw_motor_current
  // head_pitch_motor_current
  // agv_current
  // left_end_voltage
  // right_end_voltage
  // waist_pitch_motor_voltage
  // lift_motor_voltage
  // head_yaw_motor_voltage
  // head_pitch_motor_voltage
  // agv_voltage
  // emergency_stop_err_fedback
  // power_board_software_version
  if (!rosidl_runtime_c__String__init(&msg->power_board_software_version)) {
    genie_msgs__msg__PeriStatus__fini(msg);
    return false;
  }
  // power_board_hardware_version
  if (!rosidl_runtime_c__String__init(&msg->power_board_hardware_version)) {
    genie_msgs__msg__PeriStatus__fini(msg);
    return false;
  }
  // power_board_serial_number
  if (!rosidl_runtime_c__String__init(&msg->power_board_serial_number)) {
    genie_msgs__msg__PeriStatus__fini(msg);
    return false;
  }
  return true;
}

void
genie_msgs__msg__PeriStatus__fini(genie_msgs__msg__PeriStatus * msg)
{
  if (!msg) {
    return;
  }
  // header
  std_msgs__msg__Header__fini(&msg->header);
  // shut_down_compute_center_request
  // soft_emergency_stop_feedback
  // pedal_emergency_stop
  // button_emergency_stop
  // hub1_reset_request_feedback
  // hub2_reset_request_feedback
  // left_arm_reset_request_feedback
  // right_arm_reset_request_feedback
  // left_end_reset_request_feedback
  // right_end_reset_request_feedback
  // waist_pitch_motor_reset_request_feedback
  // lift_motor_reset_request_feedback
  // head_yaw_motor_reset_request_feedback
  // head_pitch_motor_reset_request_feedback
  // agv_reset_request_feedback
  // power_pcb_work_mode
  // feature_status
  // left_arm_power_ctrl_req_feedback
  // right_arm_power_ctrl_req_feedback
  // left_end_power_ctrl_req_feedback
  // right_end_power_ctrl_req_feedback
  // waist_pitch_motor_power_ctrl_req_feedback
  // lift_motor_power_ctrl_req_feedback
  // head_yaw_motor_power_ctrl_req_feedback
  // head_pitch_motor_power_ctrl_req_feedback
  // agv_power_ctrl_req_feedback
  // power_ctrl_req_failreason
  // left_end_current
  // right_end_current
  // waist_pitch_motor_current
  // lift_motor_current
  // head_yaw_motor_current
  // head_pitch_motor_current
  // agv_current
  // left_end_voltage
  // right_end_voltage
  // waist_pitch_motor_voltage
  // lift_motor_voltage
  // head_yaw_motor_voltage
  // head_pitch_motor_voltage
  // agv_voltage
  // emergency_stop_err_fedback
  // power_board_software_version
  rosidl_runtime_c__String__fini(&msg->power_board_software_version);
  // power_board_hardware_version
  rosidl_runtime_c__String__fini(&msg->power_board_hardware_version);
  // power_board_serial_number
  rosidl_runtime_c__String__fini(&msg->power_board_serial_number);
}

bool
genie_msgs__msg__PeriStatus__are_equal(const genie_msgs__msg__PeriStatus * lhs, const genie_msgs__msg__PeriStatus * rhs)
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
  // shut_down_compute_center_request
  if (lhs->shut_down_compute_center_request != rhs->shut_down_compute_center_request) {
    return false;
  }
  // soft_emergency_stop_feedback
  if (lhs->soft_emergency_stop_feedback != rhs->soft_emergency_stop_feedback) {
    return false;
  }
  // pedal_emergency_stop
  if (lhs->pedal_emergency_stop != rhs->pedal_emergency_stop) {
    return false;
  }
  // button_emergency_stop
  if (lhs->button_emergency_stop != rhs->button_emergency_stop) {
    return false;
  }
  // hub1_reset_request_feedback
  if (lhs->hub1_reset_request_feedback != rhs->hub1_reset_request_feedback) {
    return false;
  }
  // hub2_reset_request_feedback
  if (lhs->hub2_reset_request_feedback != rhs->hub2_reset_request_feedback) {
    return false;
  }
  // left_arm_reset_request_feedback
  if (lhs->left_arm_reset_request_feedback != rhs->left_arm_reset_request_feedback) {
    return false;
  }
  // right_arm_reset_request_feedback
  if (lhs->right_arm_reset_request_feedback != rhs->right_arm_reset_request_feedback) {
    return false;
  }
  // left_end_reset_request_feedback
  if (lhs->left_end_reset_request_feedback != rhs->left_end_reset_request_feedback) {
    return false;
  }
  // right_end_reset_request_feedback
  if (lhs->right_end_reset_request_feedback != rhs->right_end_reset_request_feedback) {
    return false;
  }
  // waist_pitch_motor_reset_request_feedback
  if (lhs->waist_pitch_motor_reset_request_feedback != rhs->waist_pitch_motor_reset_request_feedback) {
    return false;
  }
  // lift_motor_reset_request_feedback
  if (lhs->lift_motor_reset_request_feedback != rhs->lift_motor_reset_request_feedback) {
    return false;
  }
  // head_yaw_motor_reset_request_feedback
  if (lhs->head_yaw_motor_reset_request_feedback != rhs->head_yaw_motor_reset_request_feedback) {
    return false;
  }
  // head_pitch_motor_reset_request_feedback
  if (lhs->head_pitch_motor_reset_request_feedback != rhs->head_pitch_motor_reset_request_feedback) {
    return false;
  }
  // agv_reset_request_feedback
  if (lhs->agv_reset_request_feedback != rhs->agv_reset_request_feedback) {
    return false;
  }
  // power_pcb_work_mode
  if (lhs->power_pcb_work_mode != rhs->power_pcb_work_mode) {
    return false;
  }
  // feature_status
  if (lhs->feature_status != rhs->feature_status) {
    return false;
  }
  // left_arm_power_ctrl_req_feedback
  if (lhs->left_arm_power_ctrl_req_feedback != rhs->left_arm_power_ctrl_req_feedback) {
    return false;
  }
  // right_arm_power_ctrl_req_feedback
  if (lhs->right_arm_power_ctrl_req_feedback != rhs->right_arm_power_ctrl_req_feedback) {
    return false;
  }
  // left_end_power_ctrl_req_feedback
  if (lhs->left_end_power_ctrl_req_feedback != rhs->left_end_power_ctrl_req_feedback) {
    return false;
  }
  // right_end_power_ctrl_req_feedback
  if (lhs->right_end_power_ctrl_req_feedback != rhs->right_end_power_ctrl_req_feedback) {
    return false;
  }
  // waist_pitch_motor_power_ctrl_req_feedback
  if (lhs->waist_pitch_motor_power_ctrl_req_feedback != rhs->waist_pitch_motor_power_ctrl_req_feedback) {
    return false;
  }
  // lift_motor_power_ctrl_req_feedback
  if (lhs->lift_motor_power_ctrl_req_feedback != rhs->lift_motor_power_ctrl_req_feedback) {
    return false;
  }
  // head_yaw_motor_power_ctrl_req_feedback
  if (lhs->head_yaw_motor_power_ctrl_req_feedback != rhs->head_yaw_motor_power_ctrl_req_feedback) {
    return false;
  }
  // head_pitch_motor_power_ctrl_req_feedback
  if (lhs->head_pitch_motor_power_ctrl_req_feedback != rhs->head_pitch_motor_power_ctrl_req_feedback) {
    return false;
  }
  // agv_power_ctrl_req_feedback
  if (lhs->agv_power_ctrl_req_feedback != rhs->agv_power_ctrl_req_feedback) {
    return false;
  }
  // power_ctrl_req_failreason
  if (lhs->power_ctrl_req_failreason != rhs->power_ctrl_req_failreason) {
    return false;
  }
  // left_end_current
  if (lhs->left_end_current != rhs->left_end_current) {
    return false;
  }
  // right_end_current
  if (lhs->right_end_current != rhs->right_end_current) {
    return false;
  }
  // waist_pitch_motor_current
  if (lhs->waist_pitch_motor_current != rhs->waist_pitch_motor_current) {
    return false;
  }
  // lift_motor_current
  if (lhs->lift_motor_current != rhs->lift_motor_current) {
    return false;
  }
  // head_yaw_motor_current
  if (lhs->head_yaw_motor_current != rhs->head_yaw_motor_current) {
    return false;
  }
  // head_pitch_motor_current
  if (lhs->head_pitch_motor_current != rhs->head_pitch_motor_current) {
    return false;
  }
  // agv_current
  if (lhs->agv_current != rhs->agv_current) {
    return false;
  }
  // left_end_voltage
  if (lhs->left_end_voltage != rhs->left_end_voltage) {
    return false;
  }
  // right_end_voltage
  if (lhs->right_end_voltage != rhs->right_end_voltage) {
    return false;
  }
  // waist_pitch_motor_voltage
  if (lhs->waist_pitch_motor_voltage != rhs->waist_pitch_motor_voltage) {
    return false;
  }
  // lift_motor_voltage
  if (lhs->lift_motor_voltage != rhs->lift_motor_voltage) {
    return false;
  }
  // head_yaw_motor_voltage
  if (lhs->head_yaw_motor_voltage != rhs->head_yaw_motor_voltage) {
    return false;
  }
  // head_pitch_motor_voltage
  if (lhs->head_pitch_motor_voltage != rhs->head_pitch_motor_voltage) {
    return false;
  }
  // agv_voltage
  if (lhs->agv_voltage != rhs->agv_voltage) {
    return false;
  }
  // emergency_stop_err_fedback
  if (lhs->emergency_stop_err_fedback != rhs->emergency_stop_err_fedback) {
    return false;
  }
  // power_board_software_version
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->power_board_software_version), &(rhs->power_board_software_version)))
  {
    return false;
  }
  // power_board_hardware_version
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->power_board_hardware_version), &(rhs->power_board_hardware_version)))
  {
    return false;
  }
  // power_board_serial_number
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->power_board_serial_number), &(rhs->power_board_serial_number)))
  {
    return false;
  }
  return true;
}

bool
genie_msgs__msg__PeriStatus__copy(
  const genie_msgs__msg__PeriStatus * input,
  genie_msgs__msg__PeriStatus * output)
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
  // shut_down_compute_center_request
  output->shut_down_compute_center_request = input->shut_down_compute_center_request;
  // soft_emergency_stop_feedback
  output->soft_emergency_stop_feedback = input->soft_emergency_stop_feedback;
  // pedal_emergency_stop
  output->pedal_emergency_stop = input->pedal_emergency_stop;
  // button_emergency_stop
  output->button_emergency_stop = input->button_emergency_stop;
  // hub1_reset_request_feedback
  output->hub1_reset_request_feedback = input->hub1_reset_request_feedback;
  // hub2_reset_request_feedback
  output->hub2_reset_request_feedback = input->hub2_reset_request_feedback;
  // left_arm_reset_request_feedback
  output->left_arm_reset_request_feedback = input->left_arm_reset_request_feedback;
  // right_arm_reset_request_feedback
  output->right_arm_reset_request_feedback = input->right_arm_reset_request_feedback;
  // left_end_reset_request_feedback
  output->left_end_reset_request_feedback = input->left_end_reset_request_feedback;
  // right_end_reset_request_feedback
  output->right_end_reset_request_feedback = input->right_end_reset_request_feedback;
  // waist_pitch_motor_reset_request_feedback
  output->waist_pitch_motor_reset_request_feedback = input->waist_pitch_motor_reset_request_feedback;
  // lift_motor_reset_request_feedback
  output->lift_motor_reset_request_feedback = input->lift_motor_reset_request_feedback;
  // head_yaw_motor_reset_request_feedback
  output->head_yaw_motor_reset_request_feedback = input->head_yaw_motor_reset_request_feedback;
  // head_pitch_motor_reset_request_feedback
  output->head_pitch_motor_reset_request_feedback = input->head_pitch_motor_reset_request_feedback;
  // agv_reset_request_feedback
  output->agv_reset_request_feedback = input->agv_reset_request_feedback;
  // power_pcb_work_mode
  output->power_pcb_work_mode = input->power_pcb_work_mode;
  // feature_status
  output->feature_status = input->feature_status;
  // left_arm_power_ctrl_req_feedback
  output->left_arm_power_ctrl_req_feedback = input->left_arm_power_ctrl_req_feedback;
  // right_arm_power_ctrl_req_feedback
  output->right_arm_power_ctrl_req_feedback = input->right_arm_power_ctrl_req_feedback;
  // left_end_power_ctrl_req_feedback
  output->left_end_power_ctrl_req_feedback = input->left_end_power_ctrl_req_feedback;
  // right_end_power_ctrl_req_feedback
  output->right_end_power_ctrl_req_feedback = input->right_end_power_ctrl_req_feedback;
  // waist_pitch_motor_power_ctrl_req_feedback
  output->waist_pitch_motor_power_ctrl_req_feedback = input->waist_pitch_motor_power_ctrl_req_feedback;
  // lift_motor_power_ctrl_req_feedback
  output->lift_motor_power_ctrl_req_feedback = input->lift_motor_power_ctrl_req_feedback;
  // head_yaw_motor_power_ctrl_req_feedback
  output->head_yaw_motor_power_ctrl_req_feedback = input->head_yaw_motor_power_ctrl_req_feedback;
  // head_pitch_motor_power_ctrl_req_feedback
  output->head_pitch_motor_power_ctrl_req_feedback = input->head_pitch_motor_power_ctrl_req_feedback;
  // agv_power_ctrl_req_feedback
  output->agv_power_ctrl_req_feedback = input->agv_power_ctrl_req_feedback;
  // power_ctrl_req_failreason
  output->power_ctrl_req_failreason = input->power_ctrl_req_failreason;
  // left_end_current
  output->left_end_current = input->left_end_current;
  // right_end_current
  output->right_end_current = input->right_end_current;
  // waist_pitch_motor_current
  output->waist_pitch_motor_current = input->waist_pitch_motor_current;
  // lift_motor_current
  output->lift_motor_current = input->lift_motor_current;
  // head_yaw_motor_current
  output->head_yaw_motor_current = input->head_yaw_motor_current;
  // head_pitch_motor_current
  output->head_pitch_motor_current = input->head_pitch_motor_current;
  // agv_current
  output->agv_current = input->agv_current;
  // left_end_voltage
  output->left_end_voltage = input->left_end_voltage;
  // right_end_voltage
  output->right_end_voltage = input->right_end_voltage;
  // waist_pitch_motor_voltage
  output->waist_pitch_motor_voltage = input->waist_pitch_motor_voltage;
  // lift_motor_voltage
  output->lift_motor_voltage = input->lift_motor_voltage;
  // head_yaw_motor_voltage
  output->head_yaw_motor_voltage = input->head_yaw_motor_voltage;
  // head_pitch_motor_voltage
  output->head_pitch_motor_voltage = input->head_pitch_motor_voltage;
  // agv_voltage
  output->agv_voltage = input->agv_voltage;
  // emergency_stop_err_fedback
  output->emergency_stop_err_fedback = input->emergency_stop_err_fedback;
  // power_board_software_version
  if (!rosidl_runtime_c__String__copy(
      &(input->power_board_software_version), &(output->power_board_software_version)))
  {
    return false;
  }
  // power_board_hardware_version
  if (!rosidl_runtime_c__String__copy(
      &(input->power_board_hardware_version), &(output->power_board_hardware_version)))
  {
    return false;
  }
  // power_board_serial_number
  if (!rosidl_runtime_c__String__copy(
      &(input->power_board_serial_number), &(output->power_board_serial_number)))
  {
    return false;
  }
  return true;
}

genie_msgs__msg__PeriStatus *
genie_msgs__msg__PeriStatus__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__PeriStatus * msg = (genie_msgs__msg__PeriStatus *)allocator.allocate(sizeof(genie_msgs__msg__PeriStatus), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(genie_msgs__msg__PeriStatus));
  bool success = genie_msgs__msg__PeriStatus__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
genie_msgs__msg__PeriStatus__destroy(genie_msgs__msg__PeriStatus * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    genie_msgs__msg__PeriStatus__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
genie_msgs__msg__PeriStatus__Sequence__init(genie_msgs__msg__PeriStatus__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__PeriStatus * data = NULL;

  if (size) {
    data = (genie_msgs__msg__PeriStatus *)allocator.zero_allocate(size, sizeof(genie_msgs__msg__PeriStatus), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = genie_msgs__msg__PeriStatus__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        genie_msgs__msg__PeriStatus__fini(&data[i - 1]);
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
genie_msgs__msg__PeriStatus__Sequence__fini(genie_msgs__msg__PeriStatus__Sequence * array)
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
      genie_msgs__msg__PeriStatus__fini(&array->data[i]);
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

genie_msgs__msg__PeriStatus__Sequence *
genie_msgs__msg__PeriStatus__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__PeriStatus__Sequence * array = (genie_msgs__msg__PeriStatus__Sequence *)allocator.allocate(sizeof(genie_msgs__msg__PeriStatus__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = genie_msgs__msg__PeriStatus__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
genie_msgs__msg__PeriStatus__Sequence__destroy(genie_msgs__msg__PeriStatus__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    genie_msgs__msg__PeriStatus__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
genie_msgs__msg__PeriStatus__Sequence__are_equal(const genie_msgs__msg__PeriStatus__Sequence * lhs, const genie_msgs__msg__PeriStatus__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!genie_msgs__msg__PeriStatus__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
genie_msgs__msg__PeriStatus__Sequence__copy(
  const genie_msgs__msg__PeriStatus__Sequence * input,
  genie_msgs__msg__PeriStatus__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(genie_msgs__msg__PeriStatus);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    genie_msgs__msg__PeriStatus * data =
      (genie_msgs__msg__PeriStatus *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!genie_msgs__msg__PeriStatus__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          genie_msgs__msg__PeriStatus__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!genie_msgs__msg__PeriStatus__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
