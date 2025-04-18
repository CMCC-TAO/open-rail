// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:srv/NoitomSetFreq.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__NOITOM_SET_FREQ__STRUCT_H_
#define GENIE_MSGS__SRV__DETAIL__NOITOM_SET_FREQ__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

/// Struct defined in srv/NoitomSetFreq in the package genie_msgs.
typedef struct genie_msgs__srv__NoitomSetFreq_Request
{
  /// 要设置的频率（Hz）
  float frequency;
} genie_msgs__srv__NoitomSetFreq_Request;

// Struct for a sequence of genie_msgs__srv__NoitomSetFreq_Request.
typedef struct genie_msgs__srv__NoitomSetFreq_Request__Sequence
{
  genie_msgs__srv__NoitomSetFreq_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__NoitomSetFreq_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'message'
#include "rosidl_runtime_c/string.h"

/// Struct defined in srv/NoitomSetFreq in the package genie_msgs.
typedef struct genie_msgs__srv__NoitomSetFreq_Response
{
  /// 设置操作是否成功
  bool success;
  /// 当前实际频率
  float current_frequency;
  /// 操作结果描述
  rosidl_runtime_c__String message;
} genie_msgs__srv__NoitomSetFreq_Response;

// Struct for a sequence of genie_msgs__srv__NoitomSetFreq_Response.
typedef struct genie_msgs__srv__NoitomSetFreq_Response__Sequence
{
  genie_msgs__srv__NoitomSetFreq_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__NoitomSetFreq_Response__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__SRV__DETAIL__NOITOM_SET_FREQ__STRUCT_H_
