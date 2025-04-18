// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:msg/PeriCmd.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__PERI_CMD__STRUCT_H_
#define GENIE_MSGS__MSG__DETAIL__PERI_CMD__STRUCT_H_

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

/// Struct defined in msg/PeriCmd in the package genie_msgs.
typedef struct genie_msgs__msg__PeriCmd
{
  std_msgs__msg__Header header;
  /// 下电ready反馈
  uint8_t compute_center_ready_shut_down;
  /// 软急停
  uint8_t soft_emergency_stop;
  /// 重启HUB请求-当前是camera
  uint8_t hub1_reset_request;
  /// 重启HUB请求-键鼠wifi-usbdebug
  uint8_t hub2_reset_request;
  /// 左臂重启请求
  uint8_t left_arm_reset_request;
  /// 右臂重启请求
  uint8_t right_arm_reset_request;
  /// 左手/左夹爪重启请求
  uint8_t left_end_reset_request;
  /// 右手/右夹爪重启请求
  uint8_t right_end_reset_request;
  /// 腰部俯仰电机重启请求
  uint8_t waist_pitch_motor_reset_request;
  /// 升降电机重启请求
  uint8_t lift_motor_reset_request;
  /// 头部yaw电机重启请求
  uint8_t head_yaw_motor_reset_request;
  /// 头部pitch电机重启请求
  uint8_t head_pitch_motor_reset_request;
  /// agv重启请求
  uint8_t agv_reset_request;
  /// orin的工作模式
  uint8_t work_mode;
  /// orin的工作模式的具体状态
  uint8_t feature_status;
  /// 左臂开启/关闭请求
  uint8_t left_arm_power_ctrl_req;
  /// 右臂开启/关闭请求
  uint8_t right_arm_power_ctrl_req;
  /// 左手/左夹爪开启/关闭请求
  uint8_t left_end_power_ctrl_req;
  /// 右手/右夹爪开启/关闭请求
  uint8_t right_end_power_ctrl_req;
  /// 腰部俯仰电机开启/关闭请求
  uint8_t waist_pitch_motor_power_ctrl_req;
  /// 升降电机开启/关闭请求
  uint8_t lift_motor_power_ctrl_req;
  /// 头部yaw电机开启/关闭请求
  uint8_t head_yaw_motor_power_ctrl_req;
  /// 头部pitch电机开启/关闭请求
  uint8_t head_pitch_motor_power_ctrl_req;
  /// agv开启/关闭请求
  uint8_t agv_power_ctrl_req;
} genie_msgs__msg__PeriCmd;

// Struct for a sequence of genie_msgs__msg__PeriCmd.
typedef struct genie_msgs__msg__PeriCmd__Sequence
{
  genie_msgs__msg__PeriCmd * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__msg__PeriCmd__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__MSG__DETAIL__PERI_CMD__STRUCT_H_
