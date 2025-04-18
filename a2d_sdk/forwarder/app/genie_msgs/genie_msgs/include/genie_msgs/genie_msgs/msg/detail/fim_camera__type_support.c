// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from genie_msgs:msg/FimCamera.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "genie_msgs/msg/detail/fim_camera__rosidl_typesupport_introspection_c.h"
#include "genie_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "genie_msgs/msg/detail/fim_camera__functions.h"
#include "genie_msgs/msg/detail/fim_camera__struct.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/header.h"
// Member `header`
#include "std_msgs/msg/detail/header__rosidl_typesupport_introspection_c.h"
// Member `fim_camera`
// Member `err_code`
#include "rosidl_runtime_c/primitives_sequence_functions.h"
// Member `camera_name`
#include "rosidl_runtime_c/string_functions.h"

#ifdef __cplusplus
extern "C"
{
#endif

void genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__FimCamera_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  genie_msgs__msg__FimCamera__init(message_memory);
}

void genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__FimCamera_fini_function(void * message_memory)
{
  genie_msgs__msg__FimCamera__fini(message_memory);
}

size_t genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__size_function__FimCamera__fim_camera(
  const void * untyped_member)
{
  const rosidl_runtime_c__uint8__Sequence * member =
    (const rosidl_runtime_c__uint8__Sequence *)(untyped_member);
  return member->size;
}

const void * genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__get_const_function__FimCamera__fim_camera(
  const void * untyped_member, size_t index)
{
  const rosidl_runtime_c__uint8__Sequence * member =
    (const rosidl_runtime_c__uint8__Sequence *)(untyped_member);
  return &member->data[index];
}

void * genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__get_function__FimCamera__fim_camera(
  void * untyped_member, size_t index)
{
  rosidl_runtime_c__uint8__Sequence * member =
    (rosidl_runtime_c__uint8__Sequence *)(untyped_member);
  return &member->data[index];
}

void genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__fetch_function__FimCamera__fim_camera(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const uint8_t * item =
    ((const uint8_t *)
    genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__get_const_function__FimCamera__fim_camera(untyped_member, index));
  uint8_t * value =
    (uint8_t *)(untyped_value);
  *value = *item;
}

void genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__assign_function__FimCamera__fim_camera(
  void * untyped_member, size_t index, const void * untyped_value)
{
  uint8_t * item =
    ((uint8_t *)
    genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__get_function__FimCamera__fim_camera(untyped_member, index));
  const uint8_t * value =
    (const uint8_t *)(untyped_value);
  *item = *value;
}

bool genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__resize_function__FimCamera__fim_camera(
  void * untyped_member, size_t size)
{
  rosidl_runtime_c__uint8__Sequence * member =
    (rosidl_runtime_c__uint8__Sequence *)(untyped_member);
  rosidl_runtime_c__uint8__Sequence__fini(member);
  return rosidl_runtime_c__uint8__Sequence__init(member, size);
}

size_t genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__size_function__FimCamera__camera_name(
  const void * untyped_member)
{
  const rosidl_runtime_c__String__Sequence * member =
    (const rosidl_runtime_c__String__Sequence *)(untyped_member);
  return member->size;
}

const void * genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__get_const_function__FimCamera__camera_name(
  const void * untyped_member, size_t index)
{
  const rosidl_runtime_c__String__Sequence * member =
    (const rosidl_runtime_c__String__Sequence *)(untyped_member);
  return &member->data[index];
}

void * genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__get_function__FimCamera__camera_name(
  void * untyped_member, size_t index)
{
  rosidl_runtime_c__String__Sequence * member =
    (rosidl_runtime_c__String__Sequence *)(untyped_member);
  return &member->data[index];
}

void genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__fetch_function__FimCamera__camera_name(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const rosidl_runtime_c__String * item =
    ((const rosidl_runtime_c__String *)
    genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__get_const_function__FimCamera__camera_name(untyped_member, index));
  rosidl_runtime_c__String * value =
    (rosidl_runtime_c__String *)(untyped_value);
  *value = *item;
}

void genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__assign_function__FimCamera__camera_name(
  void * untyped_member, size_t index, const void * untyped_value)
{
  rosidl_runtime_c__String * item =
    ((rosidl_runtime_c__String *)
    genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__get_function__FimCamera__camera_name(untyped_member, index));
  const rosidl_runtime_c__String * value =
    (const rosidl_runtime_c__String *)(untyped_value);
  *item = *value;
}

bool genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__resize_function__FimCamera__camera_name(
  void * untyped_member, size_t size)
{
  rosidl_runtime_c__String__Sequence * member =
    (rosidl_runtime_c__String__Sequence *)(untyped_member);
  rosidl_runtime_c__String__Sequence__fini(member);
  return rosidl_runtime_c__String__Sequence__init(member, size);
}

size_t genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__size_function__FimCamera__err_code(
  const void * untyped_member)
{
  const rosidl_runtime_c__uint16__Sequence * member =
    (const rosidl_runtime_c__uint16__Sequence *)(untyped_member);
  return member->size;
}

const void * genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__get_const_function__FimCamera__err_code(
  const void * untyped_member, size_t index)
{
  const rosidl_runtime_c__uint16__Sequence * member =
    (const rosidl_runtime_c__uint16__Sequence *)(untyped_member);
  return &member->data[index];
}

void * genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__get_function__FimCamera__err_code(
  void * untyped_member, size_t index)
{
  rosidl_runtime_c__uint16__Sequence * member =
    (rosidl_runtime_c__uint16__Sequence *)(untyped_member);
  return &member->data[index];
}

void genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__fetch_function__FimCamera__err_code(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const uint16_t * item =
    ((const uint16_t *)
    genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__get_const_function__FimCamera__err_code(untyped_member, index));
  uint16_t * value =
    (uint16_t *)(untyped_value);
  *value = *item;
}

void genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__assign_function__FimCamera__err_code(
  void * untyped_member, size_t index, const void * untyped_value)
{
  uint16_t * item =
    ((uint16_t *)
    genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__get_function__FimCamera__err_code(untyped_member, index));
  const uint16_t * value =
    (const uint16_t *)(untyped_value);
  *item = *value;
}

bool genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__resize_function__FimCamera__err_code(
  void * untyped_member, size_t size)
{
  rosidl_runtime_c__uint16__Sequence * member =
    (rosidl_runtime_c__uint16__Sequence *)(untyped_member);
  rosidl_runtime_c__uint16__Sequence__fini(member);
  return rosidl_runtime_c__uint16__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__FimCamera_message_member_array[4] = {
  {
    "header",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__msg__FimCamera, header),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "fim_camera",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT8,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__msg__FimCamera, fim_camera),  // bytes offset in struct
    NULL,  // default value
    genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__size_function__FimCamera__fim_camera,  // size() function pointer
    genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__get_const_function__FimCamera__fim_camera,  // get_const(index) function pointer
    genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__get_function__FimCamera__fim_camera,  // get(index) function pointer
    genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__fetch_function__FimCamera__fim_camera,  // fetch(index, &value) function pointer
    genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__assign_function__FimCamera__fim_camera,  // assign(index, value) function pointer
    genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__resize_function__FimCamera__fim_camera  // resize(index) function pointer
  },
  {
    "camera_name",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__msg__FimCamera, camera_name),  // bytes offset in struct
    NULL,  // default value
    genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__size_function__FimCamera__camera_name,  // size() function pointer
    genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__get_const_function__FimCamera__camera_name,  // get_const(index) function pointer
    genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__get_function__FimCamera__camera_name,  // get(index) function pointer
    genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__fetch_function__FimCamera__camera_name,  // fetch(index, &value) function pointer
    genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__assign_function__FimCamera__camera_name,  // assign(index, value) function pointer
    genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__resize_function__FimCamera__camera_name  // resize(index) function pointer
  },
  {
    "err_code",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT16,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__msg__FimCamera, err_code),  // bytes offset in struct
    NULL,  // default value
    genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__size_function__FimCamera__err_code,  // size() function pointer
    genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__get_const_function__FimCamera__err_code,  // get_const(index) function pointer
    genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__get_function__FimCamera__err_code,  // get(index) function pointer
    genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__fetch_function__FimCamera__err_code,  // fetch(index, &value) function pointer
    genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__assign_function__FimCamera__err_code,  // assign(index, value) function pointer
    genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__resize_function__FimCamera__err_code  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__FimCamera_message_members = {
  "genie_msgs__msg",  // message namespace
  "FimCamera",  // message name
  4,  // number of fields
  sizeof(genie_msgs__msg__FimCamera),
  genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__FimCamera_message_member_array,  // message members
  genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__FimCamera_init_function,  // function to initialize message memory (memory has to be allocated)
  genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__FimCamera_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__FimCamera_message_type_support_handle = {
  0,
  &genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__FimCamera_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_genie_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, genie_msgs, msg, FimCamera)() {
  genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__FimCamera_message_member_array[0].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, std_msgs, msg, Header)();
  if (!genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__FimCamera_message_type_support_handle.typesupport_identifier) {
    genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__FimCamera_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &genie_msgs__msg__FimCamera__rosidl_typesupport_introspection_c__FimCamera_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
