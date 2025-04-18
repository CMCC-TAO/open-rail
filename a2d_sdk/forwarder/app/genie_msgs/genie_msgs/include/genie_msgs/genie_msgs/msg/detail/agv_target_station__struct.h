// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:msg/AGVTargetStation.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__AGV_TARGET_STATION__STRUCT_H_
#define GENIE_MSGS__MSG__DETAIL__AGV_TARGET_STATION__STRUCT_H_

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
// Member 'station_name'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/AGVTargetStation in the package genie_msgs.
typedef struct genie_msgs__msg__AGVTargetStation
{
  std_msgs__msg__Header header;
  /// 站台编号
  uint32_t station_id;
  /// 站台名
  rosidl_runtime_c__String station_name;
  /// 机构动作定义
  uint32_t station_action;
} genie_msgs__msg__AGVTargetStation;

// Struct for a sequence of genie_msgs__msg__AGVTargetStation.
typedef struct genie_msgs__msg__AGVTargetStation__Sequence
{
  genie_msgs__msg__AGVTargetStation * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__msg__AGVTargetStation__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__MSG__DETAIL__AGV_TARGET_STATION__STRUCT_H_
