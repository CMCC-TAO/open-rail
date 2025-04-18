// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:msg/Retarget.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__RETARGET__STRUCT_H_
#define GENIE_MSGS__MSG__DETAIL__RETARGET__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

/// Constant 'NONE'.
enum
{
  genie_msgs__msg__Retarget__NONE = 0
};

/// Constant 'DURAL_ARM'.
enum
{
  genie_msgs__msg__Retarget__DURAL_ARM = 1
};

/// Constant 'LEFT_ARM'.
enum
{
  genie_msgs__msg__Retarget__LEFT_ARM = 2
};

/// Constant 'RIGHT_ARM'.
enum
{
  genie_msgs__msg__Retarget__RIGHT_ARM = 3
};

/// Constant 'WAIST'.
enum
{
  genie_msgs__msg__Retarget__WAIST = 4
};

/// Constant 'HEAD'.
enum
{
  genie_msgs__msg__Retarget__HEAD = 5
};

/// Constant 'WAIST_HEAD'.
enum
{
  genie_msgs__msg__Retarget__WAIST_HEAD = 6
};

/// Constant 'VR'.
/**
  * device type
 */
enum
{
  genie_msgs__msg__Retarget__VR = 101
};

/// Constant 'MOCAP'.
enum
{
  genie_msgs__msg__Retarget__MOCAP = 102
};

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.h"
// Member 'left_ee_pose'
// Member 'right_ee_pose'
// Member 'left_upper_arm'
// Member 'right_upper_arm'
#include "geometry_msgs/msg/detail/pose__struct.h"
// Member 'body_joint_names'
#include "rosidl_runtime_c/string.h"
// Member 'body_joint_positions'
#include "rosidl_runtime_c/primitives_sequence.h"

/// Struct defined in msg/Retarget in the package genie_msgs.
/**
  * retarget pose from input device to robot
  * Group type
 */
typedef struct genie_msgs__msg__Retarget
{
  std_msgs__msg__Header header;
  /// 臂的输入类型    0~3
  uint8_t group_arms;
  /// 身体的输入类型  0、4~6
  uint8_t group_body;
  /// 输入设备类型      101~102
  uint8_t device;
  /// 左臂 SE3 Pose
  geometry_msgs__msg__Pose left_ee_pose;
  /// 右臂 SE3 Pose
  geometry_msgs__msg__Pose right_ee_pose;
  /// 左大臂 SE3 Pose
  geometry_msgs__msg__Pose left_upper_arm;
  /// 右大臂 SE3 Pose
  geometry_msgs__msg__Pose right_upper_arm;
  /// 头 腰，等关节names
  rosidl_runtime_c__String__Sequence body_joint_names;
  /// 头 腰，等关节cmd，顺序与names一致
  rosidl_runtime_c__double__Sequence body_joint_positions;
} genie_msgs__msg__Retarget;

// Struct for a sequence of genie_msgs__msg__Retarget.
typedef struct genie_msgs__msg__Retarget__Sequence
{
  genie_msgs__msg__Retarget * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__msg__Retarget__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__MSG__DETAIL__RETARGET__STRUCT_H_
