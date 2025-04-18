// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:msg/FimBody.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FIM_BODY__STRUCT_H_
#define GENIE_MSGS__MSG__DETAIL__FIM_BODY__STRUCT_H_

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

/// Struct defined in msg/FimBody in the package genie_msgs.
typedef struct genie_msgs__msg__FimBody
{
  std_msgs__msg__Header header;
  uint8_t fim_waist;
  uint16_t waist_err_code;
  uint8_t fim_lift;
  uint16_t lift_err_code;
} genie_msgs__msg__FimBody;

// Struct for a sequence of genie_msgs__msg__FimBody.
typedef struct genie_msgs__msg__FimBody__Sequence
{
  genie_msgs__msg__FimBody * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__msg__FimBody__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__MSG__DETAIL__FIM_BODY__STRUCT_H_
