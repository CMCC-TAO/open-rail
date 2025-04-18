// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:srv/ForceCal.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__FORCE_CAL__STRUCT_H_
#define GENIE_MSGS__SRV__DETAIL__FORCE_CAL__STRUCT_H_

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
// Member 'joint'
#include "rosidl_runtime_c/primitives_sequence.h"

/// Struct defined in srv/ForceCal in the package genie_msgs.
typedef struct genie_msgs__srv__ForceCal_Request
{
  std_msgs__msg__Header header;
  /// 1: 标定六维力数据
  int32_t cal_cmd;
  /// 0x00 = left | end, 0x01 = right | end, 0x02 = both
  uint32_t force_id;
  int8_t count;
  rosidl_runtime_c__float__Sequence joint;
  /// 暂时未用，默认阻塞
  bool block;
} genie_msgs__srv__ForceCal_Request;

// Struct for a sequence of genie_msgs__srv__ForceCal_Request.
typedef struct genie_msgs__srv__ForceCal_Request__Sequence
{
  genie_msgs__srv__ForceCal_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__ForceCal_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'res_header'
// already included above
// #include "std_msgs/msg/detail/header__struct.h"

/// Struct defined in srv/ForceCal in the package genie_msgs.
typedef struct genie_msgs__srv__ForceCal_Response
{
  std_msgs__msg__Header res_header;
  /// 0: success, 1: 控制器返回错误或参数错误 2:数据发送失败
  /// 3: 数据接收失败或超时 4:返回值解析失败 5:程序发生异常 6:不支持的手臂标定类型
  /// 7: 未知错误 8: 不支持的标定类型 9:不支持的标定cmd
  uint8_t exec_result;
} genie_msgs__srv__ForceCal_Response;

// Struct for a sequence of genie_msgs__srv__ForceCal_Response.
typedef struct genie_msgs__srv__ForceCal_Response__Sequence
{
  genie_msgs__srv__ForceCal_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__ForceCal_Response__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__SRV__DETAIL__FORCE_CAL__STRUCT_H_
