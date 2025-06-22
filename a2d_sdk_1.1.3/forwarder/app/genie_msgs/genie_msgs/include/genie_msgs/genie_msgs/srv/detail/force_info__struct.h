// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:srv/ForceInfo.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__FORCE_INFO__STRUCT_H_
#define GENIE_MSGS__SRV__DETAIL__FORCE_INFO__STRUCT_H_

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

/// Struct defined in srv/ForceInfo in the package genie_msgs.
typedef struct genie_msgs__srv__ForceInfo_Request
{
  std_msgs__msg__Header header;
  /// 0x00 = left | end, 0x10 = right | end
  uint32_t force_id;
} genie_msgs__srv__ForceInfo_Request;

// Struct for a sequence of genie_msgs__srv__ForceInfo_Request.
typedef struct genie_msgs__srv__ForceInfo_Request__Sequence
{
  genie_msgs__srv__ForceInfo_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__ForceInfo_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'res_header'
// already included above
// #include "std_msgs/msg/detail/header__struct.h"
// Member 'work_zero_force_data'
// Member 'tool_zero_force_data'
// Member 'zero_force_data'
#include "rosidl_runtime_c/primitives_sequence.h"

/// Struct defined in srv/ForceInfo in the package genie_msgs.
typedef struct genie_msgs__srv__ForceInfo_Response
{
  std_msgs__msg__Header res_header;
  /// 0: success, 1: failed
  uint8_t exec_result;
  /// 工作空间零力数据
  rosidl_runtime_c__double__Sequence work_zero_force_data;
  /// 工具坐标系零力数据
  rosidl_runtime_c__double__Sequence tool_zero_force_data;
  /// 零力矩数据
  rosidl_runtime_c__double__Sequence zero_force_data;
} genie_msgs__srv__ForceInfo_Response;

// Struct for a sequence of genie_msgs__srv__ForceInfo_Response.
typedef struct genie_msgs__srv__ForceInfo_Response__Sequence
{
  genie_msgs__srv__ForceInfo_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__ForceInfo_Response__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__SRV__DETAIL__FORCE_INFO__STRUCT_H_
