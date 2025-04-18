// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:srv/SetWifi.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__SET_WIFI__STRUCT_H_
#define GENIE_MSGS__SRV__DETAIL__SET_WIFI__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'ssid'
// Member 'password'
#include "rosidl_runtime_c/string.h"

/// Struct defined in srv/SetWifi in the package genie_msgs.
typedef struct genie_msgs__srv__SetWifi_Request
{
  rosidl_runtime_c__String ssid;
  rosidl_runtime_c__String password;
} genie_msgs__srv__SetWifi_Request;

// Struct for a sequence of genie_msgs__srv__SetWifi_Request.
typedef struct genie_msgs__srv__SetWifi_Request__Sequence
{
  genie_msgs__srv__SetWifi_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__SetWifi_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'message'
// already included above
// #include "rosidl_runtime_c/string.h"

/// Struct defined in srv/SetWifi in the package genie_msgs.
typedef struct genie_msgs__srv__SetWifi_Response
{
  bool success;
  rosidl_runtime_c__String message;
} genie_msgs__srv__SetWifi_Response;

// Struct for a sequence of genie_msgs__srv__SetWifi_Response.
typedef struct genie_msgs__srv__SetWifi_Response__Sequence
{
  genie_msgs__srv__SetWifi_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__SetWifi_Response__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__SRV__DETAIL__SET_WIFI__STRUCT_H_
