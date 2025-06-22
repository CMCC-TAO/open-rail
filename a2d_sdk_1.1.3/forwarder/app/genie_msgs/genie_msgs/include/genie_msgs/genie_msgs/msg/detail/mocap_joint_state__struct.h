// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:msg/MocapJointState.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__MOCAP_JOINT_STATE__STRUCT_H_
#define GENIE_MSGS__MSG__DETAIL__MOCAP_JOINT_STATE__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'name'
#include "rosidl_runtime_c/string.h"
// Member 'position'
#include "geometry_msgs/msg/detail/vector3__struct.h"
// Member 'orientation'
#include "geometry_msgs/msg/detail/quaternion__struct.h"

/// Struct defined in msg/MocapJointState in the package genie_msgs.
typedef struct genie_msgs__msg__MocapJointState
{
  rosidl_runtime_c__String name;
  /// 动捕tracker id
  uint32_t id;
  /// 状态
  uint32_t status;
  /// 错误码
  uint32_t err_code;
  geometry_msgs__msg__Vector3 position;
  geometry_msgs__msg__Quaternion orientation;
} genie_msgs__msg__MocapJointState;

// Struct for a sequence of genie_msgs__msg__MocapJointState.
typedef struct genie_msgs__msg__MocapJointState__Sequence
{
  genie_msgs__msg__MocapJointState * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__msg__MocapJointState__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__MSG__DETAIL__MOCAP_JOINT_STATE__STRUCT_H_
