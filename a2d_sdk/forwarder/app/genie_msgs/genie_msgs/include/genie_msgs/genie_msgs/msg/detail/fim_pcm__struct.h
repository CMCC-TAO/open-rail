// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:msg/FimPCM.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FIM_PCM__STRUCT_H_
#define GENIE_MSGS__MSG__DETAIL__FIM_PCM__STRUCT_H_

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

/// Struct defined in msg/FimPCM in the package genie_msgs.
typedef struct genie_msgs__msg__FimPCM
{
  std_msgs__msg__Header header;
  uint8_t fim_pcm;
  uint16_t err_code;
} genie_msgs__msg__FimPCM;

// Struct for a sequence of genie_msgs__msg__FimPCM.
typedef struct genie_msgs__msg__FimPCM__Sequence
{
  genie_msgs__msg__FimPCM * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__msg__FimPCM__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__MSG__DETAIL__FIM_PCM__STRUCT_H_
