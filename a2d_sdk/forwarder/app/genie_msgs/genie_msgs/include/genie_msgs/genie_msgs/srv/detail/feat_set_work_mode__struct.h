// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:srv/FeatSetWorkMode.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__FEAT_SET_WORK_MODE__STRUCT_H_
#define GENIE_MSGS__SRV__DETAIL__FEAT_SET_WORK_MODE__STRUCT_H_

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

/// Struct defined in srv/FeatSetWorkMode in the package genie_msgs.
typedef struct genie_msgs__srv__FeatSetWorkMode_Request
{
  std_msgs__msg__Header header;
  /// 0: uninit, 1: EOL, 2: Debug, 3: Test, 4: DataAcq, 5: Inference, 6: SDK, 7: OTA, 8: DEMO
  uint8_t work_mode;
} genie_msgs__srv__FeatSetWorkMode_Request;

// Struct for a sequence of genie_msgs__srv__FeatSetWorkMode_Request.
typedef struct genie_msgs__srv__FeatSetWorkMode_Request__Sequence
{
  genie_msgs__srv__FeatSetWorkMode_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__FeatSetWorkMode_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'res_header'
// already included above
// #include "std_msgs/msg/detail/header__struct.h"

/// Struct defined in srv/FeatSetWorkMode in the package genie_msgs.
typedef struct genie_msgs__srv__FeatSetWorkMode_Response
{
  std_msgs__msg__Header res_header;
  /// 0: success, 1: failed
  uint8_t exec_result;
} genie_msgs__srv__FeatSetWorkMode_Response;

// Struct for a sequence of genie_msgs__srv__FeatSetWorkMode_Response.
typedef struct genie_msgs__srv__FeatSetWorkMode_Response__Sequence
{
  genie_msgs__srv__FeatSetWorkMode_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__srv__FeatSetWorkMode_Response__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__SRV__DETAIL__FEAT_SET_WORK_MODE__STRUCT_H_
