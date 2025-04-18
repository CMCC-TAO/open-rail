// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:msg/VRData.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__VR_DATA__STRUCT_H_
#define GENIE_MSGS__MSG__DETAIL__VR_DATA__STRUCT_H_

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
// Member 'vr_controller_states'
#include "genie_msgs/msg/detail/vr_controller_state__struct.h"

/// Struct defined in msg/VRData in the package genie_msgs.
typedef struct genie_msgs__msg__VRData
{
  std_msgs__msg__Header header;
  /// 遥设备状态
  uint32_t status;
  /// 遥设备错误码
  uint32_t err_code;
  /// 手柄状态， 0 = left，1 = right
  genie_msgs__msg__VRControllerState__Sequence vr_controller_states;
} genie_msgs__msg__VRData;

// Struct for a sequence of genie_msgs__msg__VRData.
typedef struct genie_msgs__msg__VRData__Sequence
{
  genie_msgs__msg__VRData * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__msg__VRData__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__MSG__DETAIL__VR_DATA__STRUCT_H_
