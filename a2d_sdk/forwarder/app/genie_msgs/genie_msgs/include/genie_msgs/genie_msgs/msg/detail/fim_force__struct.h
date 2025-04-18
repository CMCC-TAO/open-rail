// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:msg/FimForce.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FIM_FORCE__STRUCT_H_
#define GENIE_MSGS__MSG__DETAIL__FIM_FORCE__STRUCT_H_

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
// Member 'fim_force'
// Member 'force_err_code'
#include "rosidl_runtime_c/primitives_sequence.h"

/// Struct defined in msg/FimForce in the package genie_msgs.
typedef struct genie_msgs__msg__FimForce
{
  std_msgs__msg__Header header;
  rosidl_runtime_c__uint8__Sequence fim_force;
  rosidl_runtime_c__uint16__Sequence force_err_code;
} genie_msgs__msg__FimForce;

// Struct for a sequence of genie_msgs__msg__FimForce.
typedef struct genie_msgs__msg__FimForce__Sequence
{
  genie_msgs__msg__FimForce * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__msg__FimForce__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__MSG__DETAIL__FIM_FORCE__STRUCT_H_
