// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:srv/FeatShutDown.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__FEAT_SHUT_DOWN__STRUCT_H_
#define GENIE_MSGS__SRV__DETAIL__FEAT_SHUT_DOWN__STRUCT_H_

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

/// Struct defined in srv/FeatShutDown in the package genie_msgs.
typedef struct genie_msgs__srv__FeatShutDown_Request
{
  std_msgs__msg__Header header;
} genie_msgs__srv__FeatShutDown_Request;

// Struct for a sequence of genie_msgs__srv__FeatShutDown_Request.
typedef struct genie_msgs__srv__FeatShutDown_Request__Sequence
{
  genie_msgs__srv__FeatShutDown_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__FeatShutDown_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'res_header'
// already included above
// #include "std_msgs/msg/detail/header__struct.h"

/// Struct defined in srv/FeatShutDown in the package genie_msgs.
typedef struct genie_msgs__srv__FeatShutDown_Response
{
  std_msgs__msg__Header res_header;
  /// 0: success, 1: failed
  uint8_t exec_result;
} genie_msgs__srv__FeatShutDown_Response;

// Struct for a sequence of genie_msgs__srv__FeatShutDown_Response.
typedef struct genie_msgs__srv__FeatShutDown_Response__Sequence
{
  genie_msgs__srv__FeatShutDown_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__FeatShutDown_Response__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__SRV__DETAIL__FEAT_SHUT_DOWN__STRUCT_H_
