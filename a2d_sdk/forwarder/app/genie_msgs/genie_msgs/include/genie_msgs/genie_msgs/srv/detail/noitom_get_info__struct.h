// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:srv/NoitomGetInfo.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__NOITOM_GET_INFO__STRUCT_H_
#define GENIE_MSGS__SRV__DETAIL__NOITOM_GET_INFO__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

/// Struct defined in srv/NoitomGetInfo in the package genie_msgs.
typedef struct genie_msgs__srv__NoitomGetInfo_Request
{
  uint8_t structure_needs_at_least_one_member;
} genie_msgs__srv__NoitomGetInfo_Request;

// Struct for a sequence of genie_msgs__srv__NoitomGetInfo_Request.
typedef struct genie_msgs__srv__NoitomGetInfo_Request__Sequence
{
  genie_msgs__srv__NoitomGetInfo_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__NoitomGetInfo_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'device_sn'
// Member 'software_version'
// Member 'hardware_date'
// Member 'default_ip'
#include "rosidl_runtime_c/string.h"

/// Struct defined in srv/NoitomGetInfo in the package genie_msgs.
typedef struct genie_msgs__srv__NoitomGetInfo_Response
{
  /// 设备SN号
  rosidl_runtime_c__String device_sn;
  /// 软件版本号
  rosidl_runtime_c__String software_version;
  /// 硬件生产日期
  rosidl_runtime_c__String hardware_date;
  /// 默认IP地址
  rosidl_runtime_c__String default_ip;
  /// 默认端口号
  uint16_t default_port;
} genie_msgs__srv__NoitomGetInfo_Response;

// Struct for a sequence of genie_msgs__srv__NoitomGetInfo_Response.
typedef struct genie_msgs__srv__NoitomGetInfo_Response__Sequence
{
  genie_msgs__srv__NoitomGetInfo_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__NoitomGetInfo_Response__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__SRV__DETAIL__NOITOM_GET_INFO__STRUCT_H_
