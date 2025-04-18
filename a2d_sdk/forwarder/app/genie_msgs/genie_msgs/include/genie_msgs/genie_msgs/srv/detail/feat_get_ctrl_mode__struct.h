// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:srv/FeatGetCtrlMode.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__FEAT_GET_CTRL_MODE__STRUCT_H_
#define GENIE_MSGS__SRV__DETAIL__FEAT_GET_CTRL_MODE__STRUCT_H_

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

/// Struct defined in srv/FeatGetCtrlMode in the package genie_msgs.
typedef struct genie_msgs__srv__FeatGetCtrlMode_Request
{
  std_msgs__msg__Header header;
} genie_msgs__srv__FeatGetCtrlMode_Request;

// Struct for a sequence of genie_msgs__srv__FeatGetCtrlMode_Request.
typedef struct genie_msgs__srv__FeatGetCtrlMode_Request__Sequence
{
  genie_msgs__srv__FeatGetCtrlMode_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__FeatGetCtrlMode_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'res_header'
// already included above
// #include "std_msgs/msg/detail/header__struct.h"

/// Struct defined in srv/FeatGetCtrlMode in the package genie_msgs.
typedef struct genie_msgs__srv__FeatGetCtrlMode_Response
{
  std_msgs__msg__Header res_header;
  /// 0: offline, 1: online
  uint8_t online;
  /// 0: vr, 1: mocap
  uint8_t remote_mode;
  /// bitwise
  /// bit0 = head
  /// bit1 = left arm
  /// bit2 = right arm
  /// bit3 = waist
  /// bit4 = lift
  /// bit5 = agv
  /// bitwise
  uint16_t ctrl_mode;
  /// 0: success, 1: failed
  uint8_t exec_result;
} genie_msgs__srv__FeatGetCtrlMode_Response;

// Struct for a sequence of genie_msgs__srv__FeatGetCtrlMode_Response.
typedef struct genie_msgs__srv__FeatGetCtrlMode_Response__Sequence
{
  genie_msgs__srv__FeatGetCtrlMode_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__FeatGetCtrlMode_Response__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__SRV__DETAIL__FEAT_GET_CTRL_MODE__STRUCT_H_
