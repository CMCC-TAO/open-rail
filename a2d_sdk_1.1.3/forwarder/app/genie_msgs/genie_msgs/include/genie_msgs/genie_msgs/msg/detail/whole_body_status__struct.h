// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:msg/WholeBodyStatus.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__WHOLE_BODY_STATUS__STRUCT_H_
#define GENIE_MSGS__MSG__DETAIL__WHOLE_BODY_STATUS__STRUCT_H_

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

/// Struct defined in msg/WholeBodyStatus in the package genie_msgs.
typedef struct genie_msgs__msg__WholeBodyStatus
{
  std_msgs__msg__Header header;
  /// 机械臂状态
  /// 右臂错误码
  uint32_t right_arm_error;
  /// 左臂错误码
  uint32_t left_arm_error;
  /// 右臂处在正在控制中
  bool right_arm_control;
  /// 左臂处在正在控制中
  bool left_arm_control;
  /// 右臂处于急停模式中
  bool right_arm_estop;
  /// 左臂处于急停模式中
  bool left_arm_estop;
  /// 末端状态
  /// 右末端错误码
  uint32_t right_end_error;
  /// 左末端错误码
  uint32_t left_end_error;
  /// 腰部状态
  /// 腰部错误码
  uint32_t waist_error;
  /// 升降状态
  /// 升降错误码
  uint32_t lift_error;
  /// 颈部状态
  /// 颈部错误码
  uint32_t neck_error;
  /// 底盘状态
  /// 底盘错误码
  uint32_t chassis_error;
} genie_msgs__msg__WholeBodyStatus;

// Struct for a sequence of genie_msgs__msg__WholeBodyStatus.
typedef struct genie_msgs__msg__WholeBodyStatus__Sequence
{
  genie_msgs__msg__WholeBodyStatus * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__msg__WholeBodyStatus__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__MSG__DETAIL__WHOLE_BODY_STATUS__STRUCT_H_
