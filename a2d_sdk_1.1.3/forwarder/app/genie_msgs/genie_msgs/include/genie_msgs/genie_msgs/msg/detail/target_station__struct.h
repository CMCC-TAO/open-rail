// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:msg/TargetStation.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__TARGET_STATION__STRUCT_H_
#define GENIE_MSGS__MSG__DETAIL__TARGET_STATION__STRUCT_H_

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

/// Struct defined in msg/TargetStation in the package genie_msgs.
typedef struct genie_msgs__msg__TargetStation
{
  std_msgs__msg__Header header;
  int32_t status;
} genie_msgs__msg__TargetStation;

// Struct for a sequence of genie_msgs__msg__TargetStation.
typedef struct genie_msgs__msg__TargetStation__Sequence
{
  genie_msgs__msg__TargetStation * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__msg__TargetStation__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__MSG__DETAIL__TARGET_STATION__STRUCT_H_
