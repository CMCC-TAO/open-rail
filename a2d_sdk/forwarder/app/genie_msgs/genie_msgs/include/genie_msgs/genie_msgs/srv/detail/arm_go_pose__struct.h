// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:srv/ArmGoPose.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__ARM_GO_POSE__STRUCT_H_
#define GENIE_MSGS__SRV__DETAIL__ARM_GO_POSE__STRUCT_H_

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

/// Struct defined in srv/ArmGoPose in the package genie_msgs.
typedef struct genie_msgs__srv__ArmGoPose_Request
{
  std_msgs__msg__Header header;
  /// 0 = left, 1 = right, 2 = both
  uint32_t arm_sel;
  /// 关节初始化位置
  rosidl_runtime_c__float__Sequence joint_states;
  /// true: sync, false: async
  bool block;
} genie_msgs__srv__ArmGoPose_Request;

// Struct for a sequence of genie_msgs__srv__ArmGoPose_Request.
typedef struct genie_msgs__srv__ArmGoPose_Request__Sequence
{
  genie_msgs__srv__ArmGoPose_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__ArmGoPose_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'res_header'
// already included above
// #include "std_msgs/msg/detail/header__struct.h"

/// Struct defined in srv/ArmGoPose in the package genie_msgs.
typedef struct genie_msgs__srv__ArmGoPose_Response
{
  std_msgs__msg__Header res_header;
  /// 0: success, 1: failed
  uint8_t exec_result;
} genie_msgs__srv__ArmGoPose_Response;

// Struct for a sequence of genie_msgs__srv__ArmGoPose_Response.
typedef struct genie_msgs__srv__ArmGoPose_Response__Sequence
{
  genie_msgs__srv__ArmGoPose_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__ArmGoPose_Response__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__SRV__DETAIL__ARM_GO_POSE__STRUCT_H_
