// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:msg/AGVTaskState.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__AGV_TASK_STATE__STRUCT_H_
#define GENIE_MSGS__MSG__DETAIL__AGV_TASK_STATE__STRUCT_H_

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
// Member 'task_reqid'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/AGVTaskState in the package genie_msgs.
typedef struct genie_msgs__msg__AGVTaskState
{
  std_msgs__msg__Header header;
  /// task执行id
  uint32_t task_uuid;
  /// task请求id
  rosidl_runtime_c__String task_reqid;
  /// 站台索引
  int32_t curr_station_idx;
  /// 0: 未工作 1: 工作中
  uint32_t finish_state;
} genie_msgs__msg__AGVTaskState;

// Struct for a sequence of genie_msgs__msg__AGVTaskState.
typedef struct genie_msgs__msg__AGVTaskState__Sequence
{
  genie_msgs__msg__AGVTaskState * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__msg__AGVTaskState__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__MSG__DETAIL__AGV_TASK_STATE__STRUCT_H_
