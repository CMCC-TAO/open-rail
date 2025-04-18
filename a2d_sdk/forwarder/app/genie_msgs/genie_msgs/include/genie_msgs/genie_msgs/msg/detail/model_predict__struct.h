// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:msg/ModelPredict.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__MODEL_PREDICT__STRUCT_H_
#define GENIE_MSGS__MSG__DETAIL__MODEL_PREDICT__STRUCT_H_

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
// Member 'body_joint_names'
#include "rosidl_runtime_c/string.h"
// Member 'body_joint_positions'
#include "rosidl_runtime_c/primitives_sequence.h"
// Member 'target_poses'
#include "geometry_msgs/msg/detail/pose__struct.h"
// Member 'target_joint_states'
#include "sensor_msgs/msg/detail/joint_state__struct.h"

/// Struct defined in msg/ModelPredict in the package genie_msgs.
typedef struct genie_msgs__msg__ModelPredict
{
  /// header timestamp为模型开始推理的时间
  std_msgs__msg__Header header;
  /// 头旋转 头俯仰 腰俯仰 腰升降，左臂 右臂等关节names
  rosidl_runtime_c__String__Sequence body_joint_names;
  /// 头 腰，臂等关节状态，顺序与names一致
  rosidl_runtime_c__double__Sequence body_joint_positions;
  /// 模型输出类型
  /// 0: 相对位置
  /// 1: 绝对位置
  /// 2: 绝对关节角
  /// 3: 相对关节角
  uint8_t model_output_type;
  /// pose数组
  geometry_msgs__msg__Pose__Sequence target_poses;
  /// 输出目标关节角数组
  sensor_msgs__msg__JointState__Sequence target_joint_states;
  /// 两帧之间的等待时间
  double model_sleep_time;
  /// 单帧输出的轨迹参考时间
  double trajectory_reference_time;
} genie_msgs__msg__ModelPredict;

// Struct for a sequence of genie_msgs__msg__ModelPredict.
typedef struct genie_msgs__msg__ModelPredict__Sequence
{
  genie_msgs__msg__ModelPredict * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__msg__ModelPredict__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__MSG__DETAIL__MODEL_PREDICT__STRUCT_H_
