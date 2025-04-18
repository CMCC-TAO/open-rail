// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:srv/WbcStop.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__WBC_STOP__STRUCT_H_
#define GENIE_MSGS__SRV__DETAIL__WBC_STOP__STRUCT_H_

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

/// Struct defined in srv/WbcStop in the package genie_msgs.
typedef struct genie_msgs__srv__WbcStop_Request
{
  std_msgs__msg__Header header;
} genie_msgs__srv__WbcStop_Request;

// Struct for a sequence of genie_msgs__srv__WbcStop_Request.
typedef struct genie_msgs__srv__WbcStop_Request__Sequence
{
  genie_msgs__srv__WbcStop_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__WbcStop_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'res_header'
// already included above
// #include "std_msgs/msg/detail/header__struct.h"

/// Struct defined in srv/WbcStop in the package genie_msgs.
typedef struct genie_msgs__srv__WbcStop_Response
{
  std_msgs__msg__Header res_header;
  bool stop_flag;
} genie_msgs__srv__WbcStop_Response;

// Struct for a sequence of genie_msgs__srv__WbcStop_Response.
typedef struct genie_msgs__srv__WbcStop_Response__Sequence
{
  genie_msgs__srv__WbcStop_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__WbcStop_Response__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__SRV__DETAIL__WBC_STOP__STRUCT_H_
