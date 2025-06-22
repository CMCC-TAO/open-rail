// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:srv/EndControl.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__END_CONTROL__STRUCT_H_
#define GENIE_MSGS__SRV__DETAIL__END_CONTROL__STRUCT_H_

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

/// Struct defined in srv/EndControl in the package genie_msgs.
typedef struct genie_msgs__srv__EndControl_Request
{
  std_msgs__msg__Header header;
  /// 0 = left, 1 = right, 2 = both
  uint32_t end_sel;
  /// false: 不控制, true: 控制
  bool control;
} genie_msgs__srv__EndControl_Request;

// Struct for a sequence of genie_msgs__srv__EndControl_Request.
typedef struct genie_msgs__srv__EndControl_Request__Sequence
{
  genie_msgs__srv__EndControl_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__EndControl_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'res_header'
// already included above
// #include "std_msgs/msg/detail/header__struct.h"

/// Struct defined in srv/EndControl in the package genie_msgs.
typedef struct genie_msgs__srv__EndControl_Response
{
  std_msgs__msg__Header res_header;
  /// 0: success, 1: failed
  uint8_t exec_result;
} genie_msgs__srv__EndControl_Response;

// Struct for a sequence of genie_msgs__srv__EndControl_Response.
typedef struct genie_msgs__srv__EndControl_Response__Sequence
{
  genie_msgs__srv__EndControl_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__EndControl_Response__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__SRV__DETAIL__END_CONTROL__STRUCT_H_
