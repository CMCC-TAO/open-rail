// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:msg/FaultDescription.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FAULT_DESCRIPTION__STRUCT_H_
#define GENIE_MSGS__MSG__DETAIL__FAULT_DESCRIPTION__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'error_id'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/FaultDescription in the package genie_msgs.
typedef struct genie_msgs__msg__FaultDescription
{
  rosidl_runtime_c__String error_id;
  uint16_t error_code;
} genie_msgs__msg__FaultDescription;

// Struct for a sequence of genie_msgs__msg__FaultDescription.
typedef struct genie_msgs__msg__FaultDescription__Sequence
{
  genie_msgs__msg__FaultDescription * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__msg__FaultDescription__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__MSG__DETAIL__FAULT_DESCRIPTION__STRUCT_H_
