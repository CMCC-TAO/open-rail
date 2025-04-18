// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:msg/FimArm.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FIM_ARM__STRUCT_H_
#define GENIE_MSGS__MSG__DETAIL__FIM_ARM__STRUCT_H_

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
// Member 'fim_arm'
// Member 'arm_err_code'
#include "rosidl_runtime_c/primitives_sequence.h"

/// Struct defined in msg/FimArm in the package genie_msgs.
typedef struct genie_msgs__msg__FimArm
{
  std_msgs__msg__Header header;
  rosidl_runtime_c__uint8__Sequence fim_arm;
  rosidl_runtime_c__uint16__Sequence arm_err_code;
} genie_msgs__msg__FimArm;

// Struct for a sequence of genie_msgs__msg__FimArm.
typedef struct genie_msgs__msg__FimArm__Sequence
{
  genie_msgs__msg__FimArm * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__msg__FimArm__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__MSG__DETAIL__FIM_ARM__STRUCT_H_
