// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:srv/BodyPose.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__BODY_POSE__STRUCT_H_
#define GENIE_MSGS__SRV__DETAIL__BODY_POSE__STRUCT_H_

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
// Member 'joint_states'
#include "rosidl_runtime_c/primitives_sequence.h"

/// Struct defined in srv/BodyPose in the package genie_msgs.
typedef struct genie_msgs__srv__BodyPose_Request
{
  std_msgs__msg__Header header;
  int32_t joint_flag;
  /// 关节初始化位置
  rosidl_runtime_c__float__Sequence joint_states;
  /// true: sync, false: async
  bool block;
} genie_msgs__srv__BodyPose_Request;

// Struct for a sequence of genie_msgs__srv__BodyPose_Request.
typedef struct genie_msgs__srv__BodyPose_Request__Sequence
{
  genie_msgs__srv__BodyPose_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__BodyPose_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'res_header'
// already included above
// #include "std_msgs/msg/detail/header__struct.h"

/// Struct defined in srv/BodyPose in the package genie_msgs.
typedef struct genie_msgs__srv__BodyPose_Response
{
  std_msgs__msg__Header res_header;
  /// 0: success, 1: failed
  uint8_t exec_result;
} genie_msgs__srv__BodyPose_Response;

// Struct for a sequence of genie_msgs__srv__BodyPose_Response.
typedef struct genie_msgs__srv__BodyPose_Response__Sequence
{
  genie_msgs__srv__BodyPose_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__BodyPose_Response__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__SRV__DETAIL__BODY_POSE__STRUCT_H_
