// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:srv/AGVSetColor.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__AGV_SET_COLOR__STRUCT_H_
#define GENIE_MSGS__SRV__DETAIL__AGV_SET_COLOR__STRUCT_H_

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
// Member 'color_rgba'
#include "rosidl_runtime_c/primitives_sequence.h"

/// Struct defined in srv/AGVSetColor in the package genie_msgs.
typedef struct genie_msgs__srv__AGVSetColor_Request
{
  std_msgs__msg__Header header;
  /// 0 = r, 1 = g, 2 = b, 3 = a
  rosidl_runtime_c__uint8__Sequence color_rgba;
  /// 0: off, 1: on, 2: blink 3: breath
  uint8_t ctrl_mode;
  /// blink or breath frequency
  float freqency;
} genie_msgs__srv__AGVSetColor_Request;

// Struct for a sequence of genie_msgs__srv__AGVSetColor_Request.
typedef struct genie_msgs__srv__AGVSetColor_Request__Sequence
{
  genie_msgs__srv__AGVSetColor_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__AGVSetColor_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'res_header'
// already included above
// #include "std_msgs/msg/detail/header__struct.h"

/// Struct defined in srv/AGVSetColor in the package genie_msgs.
typedef struct genie_msgs__srv__AGVSetColor_Response
{
  std_msgs__msg__Header res_header;
  /// 0: success, 1: failed
  uint8_t exec_result;
} genie_msgs__srv__AGVSetColor_Response;

// Struct for a sequence of genie_msgs__srv__AGVSetColor_Response.
typedef struct genie_msgs__srv__AGVSetColor_Response__Sequence
{
  genie_msgs__srv__AGVSetColor_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__AGVSetColor_Response__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__SRV__DETAIL__AGV_SET_COLOR__STRUCT_H_
