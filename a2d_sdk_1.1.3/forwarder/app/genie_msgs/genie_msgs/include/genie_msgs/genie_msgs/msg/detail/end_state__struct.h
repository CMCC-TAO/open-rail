// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:msg/EndState.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__END_STATE__STRUCT_H_
#define GENIE_MSGS__MSG__DETAIL__END_STATE__STRUCT_H_

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
// Member 'end_state'
#include "genie_msgs/msg/detail/motor_state__struct.h"

/// Struct defined in msg/EndState in the package genie_msgs.
typedef struct genie_msgs__msg__EndState
{
  std_msgs__msg__Header header;
  /// true表示正在控制状态
  bool controlled;
  /// 末端状态
  genie_msgs__msg__MotorState__Sequence end_state;
} genie_msgs__msg__EndState;

// Struct for a sequence of genie_msgs__msg__EndState.
typedef struct genie_msgs__msg__EndState__Sequence
{
  genie_msgs__msg__EndState * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__msg__EndState__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__MSG__DETAIL__END_STATE__STRUCT_H_
