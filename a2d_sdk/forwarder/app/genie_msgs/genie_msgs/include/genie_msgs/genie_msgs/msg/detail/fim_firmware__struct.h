// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:msg/FimFirmware.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FIM_FIRMWARE__STRUCT_H_
#define GENIE_MSGS__MSG__DETAIL__FIM_FIRMWARE__STRUCT_H_

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

/// Struct defined in msg/FimFirmware in the package genie_msgs.
typedef struct genie_msgs__msg__FimFirmware
{
  std_msgs__msg__Header header;
  uint8_t fim_fw;
  /// fim_fw_byte bit-wise
  /// bit0: meta.json丢失
  /// bit1: 相机标定文件损坏
  /// bit2: nvme磁盘空间不足
  /// bit3: nvme未挂载
  uint32_t err_code_byte;
} genie_msgs__msg__FimFirmware;

// Struct for a sequence of genie_msgs__msg__FimFirmware.
typedef struct genie_msgs__msg__FimFirmware__Sequence
{
  genie_msgs__msg__FimFirmware * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__msg__FimFirmware__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__MSG__DETAIL__FIM_FIRMWARE__STRUCT_H_
