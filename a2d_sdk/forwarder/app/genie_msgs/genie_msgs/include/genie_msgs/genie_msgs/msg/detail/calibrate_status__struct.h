// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:msg/CalibrateStatus.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__CALIBRATE_STATUS__STRUCT_H_
#define GENIE_MSGS__MSG__DETAIL__CALIBRATE_STATUS__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

/// Struct defined in msg/CalibrateStatus in the package genie_msgs.
typedef struct genie_msgs__msg__CalibrateStatus
{
  uint8_t structure_needs_at_least_one_member;
} genie_msgs__msg__CalibrateStatus;

// Struct for a sequence of genie_msgs__msg__CalibrateStatus.
typedef struct genie_msgs__msg__CalibrateStatus__Sequence
{
  genie_msgs__msg__CalibrateStatus * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__msg__CalibrateStatus__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__MSG__DETAIL__CALIBRATE_STATUS__STRUCT_H_
