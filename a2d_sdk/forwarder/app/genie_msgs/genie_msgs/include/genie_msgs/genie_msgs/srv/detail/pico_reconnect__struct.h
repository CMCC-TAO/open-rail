// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:srv/PicoReconnect.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__PICO_RECONNECT__STRUCT_H_
#define GENIE_MSGS__SRV__DETAIL__PICO_RECONNECT__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

/// Struct defined in srv/PicoReconnect in the package genie_msgs.
typedef struct genie_msgs__srv__PicoReconnect_Request
{
  uint8_t structure_needs_at_least_one_member;
} genie_msgs__srv__PicoReconnect_Request;

// Struct for a sequence of genie_msgs__srv__PicoReconnect_Request.
typedef struct genie_msgs__srv__PicoReconnect_Request__Sequence
{
  genie_msgs__srv__PicoReconnect_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__PicoReconnect_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'message'
#include "rosidl_runtime_c/string.h"

/// Struct defined in srv/PicoReconnect in the package genie_msgs.
typedef struct genie_msgs__srv__PicoReconnect_Response
{
  /// 连接操作是否成功
  bool success;
  /// 操作结果描述
  rosidl_runtime_c__String message;
} genie_msgs__srv__PicoReconnect_Response;

// Struct for a sequence of genie_msgs__srv__PicoReconnect_Response.
typedef struct genie_msgs__srv__PicoReconnect_Response__Sequence
{
  genie_msgs__srv__PicoReconnect_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__PicoReconnect_Response__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__SRV__DETAIL__PICO_RECONNECT__STRUCT_H_
