// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:msg/FeatureStatus.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FEATURE_STATUS__STRUCT_H_
#define GENIE_MSGS__MSG__DETAIL__FEATURE_STATUS__STRUCT_H_

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

/// Struct defined in msg/FeatureStatus in the package genie_msgs.
typedef struct genie_msgs__msg__FeatureStatus
{
  std_msgs__msg__Header header;
  /// 0: uninit, 1: EOL, 2: Debug, 3: Test, 4: DataAcq, 5: Inference, 6: SDK, 7: OTA, 8: DEMO
  uint8_t work_mode;
  /// 0: uninit, 1: initilizing, 2: running, 3: stopping, 4: error
  uint8_t feature_status;
} genie_msgs__msg__FeatureStatus;

// Struct for a sequence of genie_msgs__msg__FeatureStatus.
typedef struct genie_msgs__msg__FeatureStatus__Sequence
{
  genie_msgs__msg__FeatureStatus * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__msg__FeatureStatus__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__MSG__DETAIL__FEATURE_STATUS__STRUCT_H_
