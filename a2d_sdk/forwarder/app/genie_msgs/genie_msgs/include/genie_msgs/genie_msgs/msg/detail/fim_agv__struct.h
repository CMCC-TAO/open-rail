// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:msg/FimAGV.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FIM_AGV__STRUCT_H_
#define GENIE_MSGS__MSG__DETAIL__FIM_AGV__STRUCT_H_

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

/// Struct defined in msg/FimAGV in the package genie_msgs.
typedef struct genie_msgs__msg__FimAGV
{
  std_msgs__msg__Header header;
  /// 0:normal 1:error 2:unconnected
  uint8_t fim_agv;
  uint16_t agv_err_code;
} genie_msgs__msg__FimAGV;

// Struct for a sequence of genie_msgs__msg__FimAGV.
typedef struct genie_msgs__msg__FimAGV__Sequence
{
  genie_msgs__msg__FimAGV * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__msg__FimAGV__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__MSG__DETAIL__FIM_AGV__STRUCT_H_
