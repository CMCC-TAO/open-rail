// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:msg/AGVDetect.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__AGV_DETECT__STRUCT_H_
#define GENIE_MSGS__MSG__DETAIL__AGV_DETECT__STRUCT_H_

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

/// Struct defined in msg/AGVDetect in the package genie_msgs.
typedef struct genie_msgs__msg__AGVDetect
{
  std_msgs__msg__Header header;
  int32_t status;
  uint32_t err_code;
  /// 是否检测到障碍物
  bool obs_valid;
  /// 障碍物置信度
  float obs_conf;
} genie_msgs__msg__AGVDetect;

// Struct for a sequence of genie_msgs__msg__AGVDetect.
typedef struct genie_msgs__msg__AGVDetect__Sequence
{
  genie_msgs__msg__AGVDetect * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__msg__AGVDetect__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__MSG__DETAIL__AGV_DETECT__STRUCT_H_
