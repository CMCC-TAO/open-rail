// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from genie_msgs:srv/AGVSetColor.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "genie_msgs/srv/detail/agv_set_color__rosidl_typesupport_introspection_c.h"
#include "genie_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "genie_msgs/srv/detail/agv_set_color__functions.h"
#include "genie_msgs/srv/detail/agv_set_color__struct.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/header.h"
// Member `header`
#include "std_msgs/msg/detail/header__rosidl_typesupport_introspection_c.h"
// Member `color_rgba`
#include "rosidl_runtime_c/primitives_sequence_functions.h"

#ifdef __cplusplus
extern "C"
{
#endif

void genie_msgs__srv__AGVSetColor_Request__rosidl_typesupport_introspection_c__AGVSetColor_Request_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  genie_msgs__srv__AGVSetColor_Request__init(message_memory);
}

void genie_msgs__srv__AGVSetColor_Request__rosidl_typesupport_introspection_c__AGVSetColor_Request_fini_function(void * message_memory)
{
  genie_msgs__srv__AGVSetColor_Request__fini(message_memory);
}

size_t genie_msgs__srv__AGVSetColor_Request__rosidl_typesupport_introspection_c__size_function__AGVSetColor_Request__color_rgba(
  const void * untyped_member)
{
  const rosidl_runtime_c__uint8__Sequence * member =
    (const rosidl_runtime_c__uint8__Sequence *)(untyped_member);
  return member->size;
}

const void * genie_msgs__srv__AGVSetColor_Request__rosidl_typesupport_introspection_c__get_const_function__AGVSetColor_Request__color_rgba(
  const void * untyped_member, size_t index)
{
  const rosidl_runtime_c__uint8__Sequence * member =
    (const rosidl_runtime_c__uint8__Sequence *)(untyped_member);
  return &member->data[index];
}

void * genie_msgs__srv__AGVSetColor_Request__rosidl_typesupport_introspection_c__get_function__AGVSetColor_Request__color_rgba(
  void * untyped_member, size_t index)
{
  rosidl_runtime_c__uint8__Sequence * member =
    (rosidl_runtime_c__uint8__Sequence *)(untyped_member);
  return &member->data[index];
}

void genie_msgs__srv__AGVSetColor_Request__rosidl_typesupport_introspection_c__fetch_function__AGVSetColor_Request__color_rgba(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const uint8_t * item =
    ((const uint8_t *)
    genie_msgs__srv__AGVSetColor_Request__rosidl_typesupport_introspection_c__get_const_function__AGVSetColor_Request__color_rgba(untyped_member, index));
  uint8_t * value =
    (uint8_t *)(untyped_value);
  *value = *item;
}

void genie_msgs__srv__AGVSetColor_Request__rosidl_typesupport_introspection_c__assign_function__AGVSetColor_Request__color_rgba(
  void * untyped_member, size_t index, const void * untyped_value)
{
  uint8_t * item =
    ((uint8_t *)
    genie_msgs__srv__AGVSetColor_Request__rosidl_typesupport_introspection_c__get_function__AGVSetColor_Request__color_rgba(untyped_member, index));
  const uint8_t * value =
    (const uint8_t *)(untyped_value);
  *item = *value;
}

bool genie_msgs__srv__AGVSetColor_Request__rosidl_typesupport_introspection_c__resize_function__AGVSetColor_Request__color_rgba(
  void * untyped_member, size_t size)
{
  rosidl_runtime_c__uint8__Sequence * member =
    (rosidl_runtime_c__uint8__Sequence *)(untyped_member);
  rosidl_runtime_c__uint8__Sequence__fini(member);
  return rosidl_runtime_c__uint8__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember genie_msgs__srv__AGVSetColor_Request__rosidl_typesupport_introspection_c__AGVSetColor_Request_message_member_array[4] = {
  {
    "header",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__srv__AGVSetColor_Request, header),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "color_rgba",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT8,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__srv__AGVSetColor_Request, color_rgba),  // bytes offset in struct
    NULL,  // default value
    genie_msgs__srv__AGVSetColor_Request__rosidl_typesupport_introspection_c__size_function__AGVSetColor_Request__color_rgba,  // size() function pointer
    genie_msgs__srv__AGVSetColor_Request__rosidl_typesupport_introspection_c__get_const_function__AGVSetColor_Request__color_rgba,  // get_const(index) function pointer
    genie_msgs__srv__AGVSetColor_Request__rosidl_typesupport_introspection_c__get_function__AGVSetColor_Request__color_rgba,  // get(index) function pointer
    genie_msgs__srv__AGVSetColor_Request__rosidl_typesupport_introspection_c__fetch_function__AGVSetColor_Request__color_rgba,  // fetch(index, &value) function pointer
    genie_msgs__srv__AGVSetColor_Request__rosidl_typesupport_introspection_c__assign_function__AGVSetColor_Request__color_rgba,  // assign(index, value) function pointer
    genie_msgs__srv__AGVSetColor_Request__rosidl_typesupport_introspection_c__resize_function__AGVSetColor_Request__color_rgba  // resize(index) function pointer
  },
  {
    "ctrl_mode",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT8,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__srv__AGVSetColor_Request, ctrl_mode),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "freqency",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__srv__AGVSetColor_Request, freqency),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers genie_msgs__srv__AGVSetColor_Request__rosidl_typesupport_introspection_c__AGVSetColor_Request_message_members = {
  "genie_msgs__srv",  // message namespace
  "AGVSetColor_Request",  // message name
  4,  // number of fields
  sizeof(genie_msgs__srv__AGVSetColor_Request),
  genie_msgs__srv__AGVSetColor_Request__rosidl_typesupport_introspection_c__AGVSetColor_Request_message_member_array,  // message members
  genie_msgs__srv__AGVSetColor_Request__rosidl_typesupport_introspection_c__AGVSetColor_Request_init_function,  // function to initialize message memory (memory has to be allocated)
  genie_msgs__srv__AGVSetColor_Request__rosidl_typesupport_introspection_c__AGVSetColor_Request_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t genie_msgs__srv__AGVSetColor_Request__rosidl_typesupport_introspection_c__AGVSetColor_Request_message_type_support_handle = {
  0,
  &genie_msgs__srv__AGVSetColor_Request__rosidl_typesupport_introspection_c__AGVSetColor_Request_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_genie_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, genie_msgs, srv, AGVSetColor_Request)() {
  genie_msgs__srv__AGVSetColor_Request__rosidl_typesupport_introspection_c__AGVSetColor_Request_message_member_array[0].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, std_msgs, msg, Header)();
  if (!genie_msgs__srv__AGVSetColor_Request__rosidl_typesupport_introspection_c__AGVSetColor_Request_message_type_support_handle.typesupport_identifier) {
    genie_msgs__srv__AGVSetColor_Request__rosidl_typesupport_introspection_c__AGVSetColor_Request_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &genie_msgs__srv__AGVSetColor_Request__rosidl_typesupport_introspection_c__AGVSetColor_Request_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif

// already included above
// #include <stddef.h>
// already included above
// #include "genie_msgs/srv/detail/agv_set_color__rosidl_typesupport_introspection_c.h"
// already included above
// #include "genie_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
// already included above
// #include "rosidl_typesupport_introspection_c/field_types.h"
// already included above
// #include "rosidl_typesupport_introspection_c/identifier.h"
// already included above
// #include "rosidl_typesupport_introspection_c/message_introspection.h"
// already included above
// #include "genie_msgs/srv/detail/agv_set_color__functions.h"
// already included above
// #include "genie_msgs/srv/detail/agv_set_color__struct.h"


// Include directives for member types
// Member `res_header`
// already included above
// #include "std_msgs/msg/header.h"
// Member `res_header`
// already included above
// #include "std_msgs/msg/detail/header__rosidl_typesupport_introspection_c.h"

#ifdef __cplusplus
extern "C"
{
#endif

void genie_msgs__srv__AGVSetColor_Response__rosidl_typesupport_introspection_c__AGVSetColor_Response_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  genie_msgs__srv__AGVSetColor_Response__init(message_memory);
}

void genie_msgs__srv__AGVSetColor_Response__rosidl_typesupport_introspection_c__AGVSetColor_Response_fini_function(void * message_memory)
{
  genie_msgs__srv__AGVSetColor_Response__fini(message_memory);
}

static rosidl_typesupport_introspection_c__MessageMember genie_msgs__srv__AGVSetColor_Response__rosidl_typesupport_introspection_c__AGVSetColor_Response_message_member_array[2] = {
  {
    "res_header",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__srv__AGVSetColor_Response, res_header),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "exec_result",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT8,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__srv__AGVSetColor_Response, exec_result),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers genie_msgs__srv__AGVSetColor_Response__rosidl_typesupport_introspection_c__AGVSetColor_Response_message_members = {
  "genie_msgs__srv",  // message namespace
  "AGVSetColor_Response",  // message name
  2,  // number of fields
  sizeof(genie_msgs__srv__AGVSetColor_Response),
  genie_msgs__srv__AGVSetColor_Response__rosidl_typesupport_introspection_c__AGVSetColor_Response_message_member_array,  // message members
  genie_msgs__srv__AGVSetColor_Response__rosidl_typesupport_introspection_c__AGVSetColor_Response_init_function,  // function to initialize message memory (memory has to be allocated)
  genie_msgs__srv__AGVSetColor_Response__rosidl_typesupport_introspection_c__AGVSetColor_Response_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t genie_msgs__srv__AGVSetColor_Response__rosidl_typesupport_introspection_c__AGVSetColor_Response_message_type_support_handle = {
  0,
  &genie_msgs__srv__AGVSetColor_Response__rosidl_typesupport_introspection_c__AGVSetColor_Response_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_genie_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, genie_msgs, srv, AGVSetColor_Response)() {
  genie_msgs__srv__AGVSetColor_Response__rosidl_typesupport_introspection_c__AGVSetColor_Response_message_member_array[0].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, std_msgs, msg, Header)();
  if (!genie_msgs__srv__AGVSetColor_Response__rosidl_typesupport_introspection_c__AGVSetColor_Response_message_type_support_handle.typesupport_identifier) {
    genie_msgs__srv__AGVSetColor_Response__rosidl_typesupport_introspection_c__AGVSetColor_Response_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &genie_msgs__srv__AGVSetColor_Response__rosidl_typesupport_introspection_c__AGVSetColor_Response_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif

#include "rosidl_runtime_c/service_type_support_struct.h"
// already included above
// #include "genie_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
// already included above
// #include "genie_msgs/srv/detail/agv_set_color__rosidl_typesupport_introspection_c.h"
// already included above
// #include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/service_introspection.h"

// this is intentionally not const to allow initialization later to prevent an initialization race
static rosidl_typesupport_introspection_c__ServiceMembers genie_msgs__srv__detail__agv_set_color__rosidl_typesupport_introspection_c__AGVSetColor_service_members = {
  "genie_msgs__srv",  // service namespace
  "AGVSetColor",  // service name
  // these two fields are initialized below on the first access
  NULL,  // request message
  // genie_msgs__srv__detail__agv_set_color__rosidl_typesupport_introspection_c__AGVSetColor_Request_message_type_support_handle,
  NULL  // response message
  // genie_msgs__srv__detail__agv_set_color__rosidl_typesupport_introspection_c__AGVSetColor_Response_message_type_support_handle
};

static rosidl_service_type_support_t genie_msgs__srv__detail__agv_set_color__rosidl_typesupport_introspection_c__AGVSetColor_service_type_support_handle = {
  0,
  &genie_msgs__srv__detail__agv_set_color__rosidl_typesupport_introspection_c__AGVSetColor_service_members,
  get_service_typesupport_handle_function,
};

// Forward declaration of request/response type support functions
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, genie_msgs, srv, AGVSetColor_Request)();

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, genie_msgs, srv, AGVSetColor_Response)();

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_genie_msgs
const rosidl_service_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_introspection_c, genie_msgs, srv, AGVSetColor)() {
  if (!genie_msgs__srv__detail__agv_set_color__rosidl_typesupport_introspection_c__AGVSetColor_service_type_support_handle.typesupport_identifier) {
    genie_msgs__srv__detail__agv_set_color__rosidl_typesupport_introspection_c__AGVSetColor_service_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  rosidl_typesupport_introspection_c__ServiceMembers * service_members =
    (rosidl_typesupport_introspection_c__ServiceMembers *)genie_msgs__srv__detail__agv_set_color__rosidl_typesupport_introspection_c__AGVSetColor_service_type_support_handle.data;

  if (!service_members->request_members_) {
    service_members->request_members_ =
      (const rosidl_typesupport_introspection_c__MessageMembers *)
      ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, genie_msgs, srv, AGVSetColor_Request)()->data;
  }
  if (!service_members->response_members_) {
    service_members->response_members_ =
      (const rosidl_typesupport_introspection_c__MessageMembers *)
      ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, genie_msgs, srv, AGVSetColor_Response)()->data;
  }

  return &genie_msgs__srv__detail__agv_set_color__rosidl_typesupport_introspection_c__AGVSetColor_service_type_support_handle;
}
