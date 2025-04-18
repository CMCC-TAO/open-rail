// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:msg/MocapData.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__MOCAP_DATA__STRUCT_H_
#define GENIE_MSGS__MSG__DETAIL__MOCAP_DATA__STRUCT_H_

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
// Member 'mocap_joint_states'
#include "genie_msgs/msg/detail/mocap_joint_state__struct.h"

/// Struct defined in msg/MocapData in the package genie_msgs.
typedef struct genie_msgs__msg__MocapData
{
  std_msgs__msg__Header header;
  /// 遥设备状态   0: normal, 1: not calibrated
  uint32_t status;
  /// 对于手臂的状态值
  ///   kNormal                       = 0x0000 #正常
  ///   kNotCalibrated                = 0x0001 #未标定
  /// 遥设备错误码
  uint32_t err_code;
  /// 动捕或者VR手势识别的数据
  genie_msgs__msg__MocapJointState__Sequence mocap_joint_states;
} genie_msgs__msg__MocapData;

// Struct for a sequence of genie_msgs__msg__MocapData.
typedef struct genie_msgs__msg__MocapData__Sequence
{
  genie_msgs__msg__MocapData * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__msg__MocapData__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__MSG__DETAIL__MOCAP_DATA__STRUCT_H_
