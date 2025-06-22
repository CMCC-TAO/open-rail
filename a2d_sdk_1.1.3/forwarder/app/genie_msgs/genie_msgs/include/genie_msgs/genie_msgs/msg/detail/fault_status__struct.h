// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:msg/FaultStatus.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FAULT_STATUS__STRUCT_H_
#define GENIE_MSGS__MSG__DETAIL__FAULT_STATUS__STRUCT_H_

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
// Member 'faults'
#include "genie_msgs/msg/detail/fault_description__struct.h"

/// Struct defined in msg/FaultStatus in the package genie_msgs.
typedef struct genie_msgs__msg__FaultStatus
{
  /// 标准消息头
  std_msgs__msg__Header header;
  /// 故障数组
  genie_msgs__msg__FaultDescription__Sequence faults;
} genie_msgs__msg__FaultStatus;

// Struct for a sequence of genie_msgs__msg__FaultStatus.
typedef struct genie_msgs__msg__FaultStatus__Sequence
{
  genie_msgs__msg__FaultStatus * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__msg__FaultStatus__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__MSG__DETAIL__FAULT_STATUS__STRUCT_H_
