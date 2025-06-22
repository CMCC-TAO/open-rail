// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:srv/FeatSetCtrlMode.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__FEAT_SET_CTRL_MODE__STRUCT_H_
#define GENIE_MSGS__SRV__DETAIL__FEAT_SET_CTRL_MODE__STRUCT_H_

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

/// Struct defined in srv/FeatSetCtrlMode in the package genie_msgs.
typedef struct genie_msgs__srv__FeatSetCtrlMode_Request
{
  std_msgs__msg__Header header;
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
} genie_msgs__srv__FeatSetCtrlMode_Request;

// Struct for a sequence of genie_msgs__srv__FeatSetCtrlMode_Request.
typedef struct genie_msgs__srv__FeatSetCtrlMode_Request__Sequence
{
  genie_msgs__srv__FeatSetCtrlMode_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__FeatSetCtrlMode_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'res_header'
// already included above
// #include "std_msgs/msg/detail/header__struct.h"

/// Struct defined in srv/FeatSetCtrlMode in the package genie_msgs.
typedef struct genie_msgs__srv__FeatSetCtrlMode_Response
{
  std_msgs__msg__Header res_header;
  /// 0: success, 1: failed
  uint8_t exec_result;
} genie_msgs__srv__FeatSetCtrlMode_Response;

// Struct for a sequence of genie_msgs__srv__FeatSetCtrlMode_Response.
typedef struct genie_msgs__srv__FeatSetCtrlMode_Response__Sequence
{
  genie_msgs__srv__FeatSetCtrlMode_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__FeatSetCtrlMode_Response__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__SRV__DETAIL__FEAT_SET_CTRL_MODE__STRUCT_H_
