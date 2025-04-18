// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:srv/AGVCancelTask.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__AGV_CANCEL_TASK__STRUCT_H_
#define GENIE_MSGS__SRV__DETAIL__AGV_CANCEL_TASK__STRUCT_H_

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
// Member 'task_uuid'
#include "rosidl_runtime_c/string.h"

/// Struct defined in srv/AGVCancelTask in the package genie_msgs.
typedef struct genie_msgs__srv__AGVCancelTask_Request
{
  std_msgs__msg__Header header;
  /// 任务执行编号
  rosidl_runtime_c__String task_uuid;
} genie_msgs__srv__AGVCancelTask_Request;

// Struct for a sequence of genie_msgs__srv__AGVCancelTask_Request.
typedef struct genie_msgs__srv__AGVCancelTask_Request__Sequence
{
  genie_msgs__srv__AGVCancelTask_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__AGVCancelTask_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'res_header'
// already included above
// #include "std_msgs/msg/detail/header__struct.h"

/// Struct defined in srv/AGVCancelTask in the package genie_msgs.
typedef struct genie_msgs__srv__AGVCancelTask_Response
{
  std_msgs__msg__Header res_header;
  uint32_t req_result;
  /// 0:成功，其他失败
  uint32_t ret_code;
  /// 任务编号(由底盘生成）
  uint32_t task_uuid;
} genie_msgs__srv__AGVCancelTask_Response;

// Struct for a sequence of genie_msgs__srv__AGVCancelTask_Response.
typedef struct genie_msgs__srv__AGVCancelTask_Response__Sequence
{
  genie_msgs__srv__AGVCancelTask_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__AGVCancelTask_Response__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__SRV__DETAIL__AGV_CANCEL_TASK__STRUCT_H_
