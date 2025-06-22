// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:msg/PeriStatus.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__PERI_STATUS__STRUCT_H_
#define GENIE_MSGS__MSG__DETAIL__PERI_STATUS__STRUCT_H_

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
// Member 'power_board_software_version'
// Member 'power_board_hardware_version'
// Member 'power_board_serial_number'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/PeriStatus in the package genie_msgs.
typedef struct genie_msgs__msg__PeriStatus
{
  std_msgs__msg__Header header;
  /// 下电请求
  uint8_t shut_down_compute_center_request;
  /// 软急停反馈
  uint8_t soft_emergency_stop_feedback;
  /// 踏板急停信息
  uint8_t pedal_emergency_stop;
  /// 按键急停信息
  uint8_t button_emergency_stop;
  /// 重启HUB请求反馈-当前是camera
  uint8_t hub1_reset_request_feedback;
  /// 重启HUB请求反馈-键鼠wifi-usbdebug
  uint8_t hub2_reset_request_feedback;
  /// 左臂重启请求反馈
  uint8_t left_arm_reset_request_feedback;
  /// 右臂重启请求反馈
  uint8_t right_arm_reset_request_feedback;
  /// 左手/左夹爪重启请求反馈
  uint8_t left_end_reset_request_feedback;
  /// 右手/右夹爪重启请求反馈
  uint8_t right_end_reset_request_feedback;
  /// 腰部俯仰电机重启请求反馈
  uint8_t waist_pitch_motor_reset_request_feedback;
  /// 升降电机重启请求反馈
  uint8_t lift_motor_reset_request_feedback;
  /// 头部yaw电机重启请求反馈
  uint8_t head_yaw_motor_reset_request_feedback;
  /// 头部pitch电机重启请求反馈
  uint8_t head_pitch_motor_reset_request_feedback;
  /// agv重启请求反馈
  uint8_t agv_reset_request_feedback;
  /// 电源板的工作模式
  uint8_t power_pcb_work_mode;
  /// 电源板的工作模式的具体状态
  uint8_t feature_status;
  /// 左臂开启/关闭请求反馈
  uint8_t left_arm_power_ctrl_req_feedback;
  /// 右臂开启/关闭请求反馈
  uint8_t right_arm_power_ctrl_req_feedback;
  /// 左手/左夹爪开启/关闭请求反馈
  uint8_t left_end_power_ctrl_req_feedback;
  /// 右手/右夹爪开启/关闭请求反馈
  uint8_t right_end_power_ctrl_req_feedback;
  /// 腰部俯仰电机开启/关闭请求反馈
  uint8_t waist_pitch_motor_power_ctrl_req_feedback;
  /// 升降电机开启/关闭请求反馈
  uint8_t lift_motor_power_ctrl_req_feedback;
  /// 头部yaw电机开启/关闭请求反馈
  uint8_t head_yaw_motor_power_ctrl_req_feedback;
  /// 头部pitch电机开启/关闭请求反馈
  uint8_t head_pitch_motor_power_ctrl_req_feedback;
  /// agv开启/关闭请求反馈
  uint8_t agv_power_ctrl_req_feedback;
  /// 开启/关闭失败原因反馈
  uint8_t power_ctrl_req_failreason;
  /// 左臂电流
  float left_end_current;
  /// 右臂电流
  float right_end_current;
  /// 俯仰电机电流
  float waist_pitch_motor_current;
  /// 升降电机电流
  float lift_motor_current;
  /// 头部yaw电机电流
  float head_yaw_motor_current;
  /// 头部pitch电机电流
  float head_pitch_motor_current;
  /// agv电流
  float agv_current;
  /// 左臂电压
  float left_end_voltage;
  /// 右臂电压
  float right_end_voltage;
  /// 俯仰电机电压
  float waist_pitch_motor_voltage;
  /// 升降电机电压
  float lift_motor_voltage;
  /// 头部yaw电机电压
  float head_yaw_motor_voltage;
  /// 头部pitch电机电压
  float head_pitch_motor_voltage;
  /// agv电压
  float agv_voltage;
  /// 急停故障信息反馈
  uint8_t emergency_stop_err_fedback;
  /// 软件版本号
  rosidl_runtime_c__String power_board_software_version;
  /// 硬件版本号
  rosidl_runtime_c__String power_board_hardware_version;
  /// 序列号
  rosidl_runtime_c__String power_board_serial_number;
} genie_msgs__msg__PeriStatus;

// Struct for a sequence of genie_msgs__msg__PeriStatus.
typedef struct genie_msgs__msg__PeriStatus__Sequence
{
  genie_msgs__msg__PeriStatus * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__msg__PeriStatus__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__MSG__DETAIL__PERI_STATUS__STRUCT_H_
