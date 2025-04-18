// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from genie_msgs:msg/Position.idl
// generated code does not contain a copyright notice
#include "genie_msgs/msg/detail/position__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"
// Member `motor_states`
#include "genie_msgs/msg/detail/motor_state__functions.h"
// Member `agv_task_state`
#include "genie_msgs/msg/detail/agv_task_state__functions.h"

bool
genie_msgs__msg__Position__init(genie_msgs__msg__Position * msg)
{
  if (!msg) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__init(&msg->header)) {
    genie_msgs__msg__Position__fini(msg);
    return false;
  }
  // agv_status
  // position_conf
  // agv_pos_x
  // agv_pos_y
  // agv_pos_z
  // agv_angle
  // odom_x
  // odom_y
  // odom_z
  // odom_angle
  // linear_speed
  // angular_speed
  // acc_x
  // acc_y
  // acc_z
  // gyro_x
  // gyro_y
  // gyro_z
  // roll
  // pitch
  // yaw
  // motor_states
  if (!genie_msgs__msg__MotorState__Sequence__init(&msg->motor_states, 0)) {
    genie_msgs__msg__Position__fini(msg);
    return false;
  }
  // agv_task_state
  if (!genie_msgs__msg__AGVTaskState__init(&msg->agv_task_state)) {
    genie_msgs__msg__Position__fini(msg);
    return false;
  }
  return true;
}

void
genie_msgs__msg__Position__fini(genie_msgs__msg__Position * msg)
{
  if (!msg) {
    return;
  }
  // header
  std_msgs__msg__Header__fini(&msg->header);
  // agv_status
  // position_conf
  // agv_pos_x
  // agv_pos_y
  // agv_pos_z
  // agv_angle
  // odom_x
  // odom_y
  // odom_z
  // odom_angle
  // linear_speed
  // angular_speed
  // acc_x
  // acc_y
  // acc_z
  // gyro_x
  // gyro_y
  // gyro_z
  // roll
  // pitch
  // yaw
  // motor_states
  genie_msgs__msg__MotorState__Sequence__fini(&msg->motor_states);
  // agv_task_state
  genie_msgs__msg__AGVTaskState__fini(&msg->agv_task_state);
}

bool
genie_msgs__msg__Position__are_equal(const genie_msgs__msg__Position * lhs, const genie_msgs__msg__Position * rhs)
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
  // agv_status
  if (lhs->agv_status != rhs->agv_status) {
    return false;
  }
  // position_conf
  if (lhs->position_conf != rhs->position_conf) {
    return false;
  }
  // agv_pos_x
  if (lhs->agv_pos_x != rhs->agv_pos_x) {
    return false;
  }
  // agv_pos_y
  if (lhs->agv_pos_y != rhs->agv_pos_y) {
    return false;
  }
  // agv_pos_z
  if (lhs->agv_pos_z != rhs->agv_pos_z) {
    return false;
  }
  // agv_angle
  if (lhs->agv_angle != rhs->agv_angle) {
    return false;
  }
  // odom_x
  if (lhs->odom_x != rhs->odom_x) {
    return false;
  }
  // odom_y
  if (lhs->odom_y != rhs->odom_y) {
    return false;
  }
  // odom_z
  if (lhs->odom_z != rhs->odom_z) {
    return false;
  }
  // odom_angle
  if (lhs->odom_angle != rhs->odom_angle) {
    return false;
  }
  // linear_speed
  if (lhs->linear_speed != rhs->linear_speed) {
    return false;
  }
  // angular_speed
  if (lhs->angular_speed != rhs->angular_speed) {
    return false;
  }
  // acc_x
  if (lhs->acc_x != rhs->acc_x) {
    return false;
  }
  // acc_y
  if (lhs->acc_y != rhs->acc_y) {
    return false;
  }
  // acc_z
  if (lhs->acc_z != rhs->acc_z) {
    return false;
  }
  // gyro_x
  if (lhs->gyro_x != rhs->gyro_x) {
    return false;
  }
  // gyro_y
  if (lhs->gyro_y != rhs->gyro_y) {
    return false;
  }
  // gyro_z
  if (lhs->gyro_z != rhs->gyro_z) {
    return false;
  }
  // roll
  if (lhs->roll != rhs->roll) {
    return false;
  }
  // pitch
  if (lhs->pitch != rhs->pitch) {
    return false;
  }
  // yaw
  if (lhs->yaw != rhs->yaw) {
    return false;
  }
  // motor_states
  if (!genie_msgs__msg__MotorState__Sequence__are_equal(
      &(lhs->motor_states), &(rhs->motor_states)))
  {
    return false;
  }
  // agv_task_state
  if (!genie_msgs__msg__AGVTaskState__are_equal(
      &(lhs->agv_task_state), &(rhs->agv_task_state)))
  {
    return false;
  }
  return true;
}

bool
genie_msgs__msg__Position__copy(
  const genie_msgs__msg__Position * input,
  genie_msgs__msg__Position * output)
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
  // agv_status
  output->agv_status = input->agv_status;
  // position_conf
  output->position_conf = input->position_conf;
  // agv_pos_x
  output->agv_pos_x = input->agv_pos_x;
  // agv_pos_y
  output->agv_pos_y = input->agv_pos_y;
  // agv_pos_z
  output->agv_pos_z = input->agv_pos_z;
  // agv_angle
  output->agv_angle = input->agv_angle;
  // odom_x
  output->odom_x = input->odom_x;
  // odom_y
  output->odom_y = input->odom_y;
  // odom_z
  output->odom_z = input->odom_z;
  // odom_angle
  output->odom_angle = input->odom_angle;
  // linear_speed
  output->linear_speed = input->linear_speed;
  // angular_speed
  output->angular_speed = input->angular_speed;
  // acc_x
  output->acc_x = input->acc_x;
  // acc_y
  output->acc_y = input->acc_y;
  // acc_z
  output->acc_z = input->acc_z;
  // gyro_x
  output->gyro_x = input->gyro_x;
  // gyro_y
  output->gyro_y = input->gyro_y;
  // gyro_z
  output->gyro_z = input->gyro_z;
  // roll
  output->roll = input->roll;
  // pitch
  output->pitch = input->pitch;
  // yaw
  output->yaw = input->yaw;
  // motor_states
  if (!genie_msgs__msg__MotorState__Sequence__copy(
      &(input->motor_states), &(output->motor_states)))
  {
    return false;
  }
  // agv_task_state
  if (!genie_msgs__msg__AGVTaskState__copy(
      &(input->agv_task_state), &(output->agv_task_state)))
  {
    return false;
  }
  return true;
}

genie_msgs__msg__Position *
genie_msgs__msg__Position__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__Position * msg = (genie_msgs__msg__Position *)allocator.allocate(sizeof(genie_msgs__msg__Position), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(genie_msgs__msg__Position));
  bool success = genie_msgs__msg__Position__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
genie_msgs__msg__Position__destroy(genie_msgs__msg__Position * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    genie_msgs__msg__Position__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
genie_msgs__msg__Position__Sequence__init(genie_msgs__msg__Position__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__Position * data = NULL;

  if (size) {
    data = (genie_msgs__msg__Position *)allocator.zero_allocate(size, sizeof(genie_msgs__msg__Position), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = genie_msgs__msg__Position__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        genie_msgs__msg__Position__fini(&data[i - 1]);
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
genie_msgs__msg__Position__Sequence__fini(genie_msgs__msg__Position__Sequence * array)
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
      genie_msgs__msg__Position__fini(&array->data[i]);
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

genie_msgs__msg__Position__Sequence *
genie_msgs__msg__Position__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__Position__Sequence * array = (genie_msgs__msg__Position__Sequence *)allocator.allocate(sizeof(genie_msgs__msg__Position__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = genie_msgs__msg__Position__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
genie_msgs__msg__Position__Sequence__destroy(genie_msgs__msg__Position__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    genie_msgs__msg__Position__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
genie_msgs__msg__Position__Sequence__are_equal(const genie_msgs__msg__Position__Sequence * lhs, const genie_msgs__msg__Position__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!genie_msgs__msg__Position__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
genie_msgs__msg__Position__Sequence__copy(
  const genie_msgs__msg__Position__Sequence * input,
  genie_msgs__msg__Position__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(genie_msgs__msg__Position);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    genie_msgs__msg__Position * data =
      (genie_msgs__msg__Position *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!genie_msgs__msg__Position__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          genie_msgs__msg__Position__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!genie_msgs__msg__Position__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
