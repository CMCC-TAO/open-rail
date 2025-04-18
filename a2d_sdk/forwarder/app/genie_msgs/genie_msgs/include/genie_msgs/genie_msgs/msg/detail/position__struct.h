// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:msg/Position.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__POSITION__STRUCT_H_
#define GENIE_MSGS__MSG__DETAIL__POSITION__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.h"
// Member 'motor_states'
#include "genie_msgs/msg/detail/motor_state__struct.h"
// Member 'agv_task_state'
#include "genie_msgs/msg/detail/agv_task_state__struct.h"

/// Struct defined in msg/Position in the package genie_msgs.
typedef struct genie_msgs__msg__Position
{
  std_msgs__msg__Header header;
  int32_t agv_status;
  float position_conf;
  float agv_pos_x;
  float agv_pos_y;
  float agv_pos_z;
  float agv_angle;
  float odom_x;
  float odom_y;
  float odom_z;
  float odom_angle;
  float linear_speed;
  float angular_speed;
  float acc_x;
  float acc_y;
  float acc_z;
  float gyro_x;
  float gyro_y;
  float gyro_z;
  float roll;
  float pitch;
  float yaw;
  /// 底盘电机状态
  genie_msgs__msg__MotorState__Sequence motor_states;
  /// AGV任务状态
  genie_msgs__msg__AGVTaskState agv_task_state;
} genie_msgs__msg__Position;

// Struct for a sequence of genie_msgs__msg__Position.
typedef struct genie_msgs__msg__Position__Sequence
{
  genie_msgs__msg__Position * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__msg__Position__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__MSG__DETAIL__POSITION__STRUCT_H_
