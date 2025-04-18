// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:srv/RecordControl.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__RECORD_CONTROL__STRUCT_H_
#define GENIE_MSGS__SRV__DETAIL__RECORD_CONTROL__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'req_header'
#include "std_msgs/msg/detail/header__struct.h"

/// Struct defined in srv/RecordControl in the package genie_msgs.
typedef struct genie_msgs__srv__RecordControl_Request
{
  std_msgs__msg__Header req_header;
  /// false: 停止录制, true: 开始录制
  bool record;
} genie_msgs__srv__RecordControl_Request;

// Struct for a sequence of genie_msgs__srv__RecordControl_Request.
typedef struct genie_msgs__srv__RecordControl_Request__Sequence
{
  genie_msgs__srv__RecordControl_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__RecordControl_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'res_header'
// already included above
// #include "std_msgs/msg/detail/header__struct.h"

/// Struct defined in srv/RecordControl in the package genie_msgs.
typedef struct genie_msgs__srv__RecordControl_Response
{
  std_msgs__msg__Header res_header;
  /// 参考RtnType定义
  uint8_t exec_result;
} genie_msgs__srv__RecordControl_Response;

// Struct for a sequence of genie_msgs__srv__RecordControl_Response.
typedef struct genie_msgs__srv__RecordControl_Response__Sequence
{
  genie_msgs__srv__RecordControl_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__RecordControl_Response__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__SRV__DETAIL__RECORD_CONTROL__STRUCT_H_
