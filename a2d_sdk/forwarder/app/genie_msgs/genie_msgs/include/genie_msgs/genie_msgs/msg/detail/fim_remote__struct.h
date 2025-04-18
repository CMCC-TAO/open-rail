// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:msg/FimRemote.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FIM_REMOTE__STRUCT_H_
#define GENIE_MSGS__MSG__DETAIL__FIM_REMOTE__STRUCT_H_

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

/// Struct defined in msg/FimRemote in the package genie_msgs.
typedef struct genie_msgs__msg__FimRemote
{
  std_msgs__msg__Header header;
  /// 0:normal 1:error 2:unconnected 3:not used
  uint8_t fim_vr;
  uint16_t vr_err_code;
  uint8_t fim_mocap;
  uint16_t mocap_err_code;
} genie_msgs__msg__FimRemote;

// Struct for a sequence of genie_msgs__msg__FimRemote.
typedef struct genie_msgs__msg__FimRemote__Sequence
{
  genie_msgs__msg__FimRemote * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__msg__FimRemote__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__MSG__DETAIL__FIM_REMOTE__STRUCT_H_
