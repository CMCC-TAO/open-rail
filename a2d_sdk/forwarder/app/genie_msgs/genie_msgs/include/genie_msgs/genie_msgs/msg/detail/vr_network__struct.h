// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:msg/VRNetwork.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__VR_NETWORK__STRUCT_H_
#define GENIE_MSGS__MSG__DETAIL__VR_NETWORK__STRUCT_H_

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
// Member 'device_name'
// Member 'ip_address'
// Member 'remote_ip_address'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/VRNetwork in the package genie_msgs.
typedef struct genie_msgs__msg__VRNetwork
{
  std_msgs__msg__Header header;
  /// 设备名称
  rosidl_runtime_c__String device_name;
  /// 是否连接
  bool is_connected;
  /// 丢包率（百分比）
  float packet_loss_rate;
  /// 延迟（毫秒）
  float latency;
  /// 频率（赫兹）
  float frequency;
  /// IP 地址
  rosidl_runtime_c__String ip_address;
  /// 远程 IP 地址
  rosidl_runtime_c__String remote_ip_address;
} genie_msgs__msg__VRNetwork;

// Struct for a sequence of genie_msgs__msg__VRNetwork.
typedef struct genie_msgs__msg__VRNetwork__Sequence
{
  genie_msgs__msg__VRNetwork * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__msg__VRNetwork__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__MSG__DETAIL__VR_NETWORK__STRUCT_H_
