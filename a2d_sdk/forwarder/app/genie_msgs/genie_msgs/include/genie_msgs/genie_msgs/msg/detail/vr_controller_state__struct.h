// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:msg/VRControllerState.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__VR_CONTROLLER_STATE__STRUCT_H_
#define GENIE_MSGS__MSG__DETAIL__VR_CONTROLLER_STATE__STRUCT_H_

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

/// Struct defined in msg/VRControllerState in the package genie_msgs.
typedef struct genie_msgs__msg__VRControllerState
{
  /// 控制器名称（例如："left" 或 "right"）
  rosidl_runtime_c__String name;
  /// 控制器ID
  uint32_t id;
  /// 按键1状态
  bool key_one;
  /// 按键2状态
  bool key_two;
  /// 手柄扳机值
  double hand_trig;
  /// 食指扳机值
  double index_trig;
  /// 摇杆X轴值
  double axis_x;
  /// 摇杆Y轴值
  double axis_y;
  /// 摇杆按下
  bool axis_click;
  /// 控制器位置
  geometry_msgs__msg__Vector3 position;
  /// 控制器旋转（四元数）
  geometry_msgs__msg__Quaternion orientation;
} genie_msgs__msg__VRControllerState;

// Struct for a sequence of genie_msgs__msg__VRControllerState.
typedef struct genie_msgs__msg__VRControllerState__Sequence
{
  genie_msgs__msg__VRControllerState * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__msg__VRControllerState__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__MSG__DETAIL__VR_CONTROLLER_STATE__STRUCT_H_
