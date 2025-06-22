// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:msg/ButtonState.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__BUTTON_STATE__STRUCT_H_
#define GENIE_MSGS__MSG__DETAIL__BUTTON_STATE__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

/// Struct defined in msg/ButtonState in the package genie_msgs.
typedef struct genie_msgs__msg__ButtonState
{
  /// 是否按下
  bool is_pressed;
  /// 按压值
  float pressure;
} genie_msgs__msg__ButtonState;

// Struct for a sequence of genie_msgs__msg__ButtonState.
typedef struct genie_msgs__msg__ButtonState__Sequence
{
  genie_msgs__msg__ButtonState * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__msg__ButtonState__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__MSG__DETAIL__BUTTON_STATE__STRUCT_H_
