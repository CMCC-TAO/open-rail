// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from genie_msgs:msg/FimArm.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "genie_msgs/msg/detail/fim_arm__rosidl_typesupport_introspection_c.h"
#include "genie_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "genie_msgs/msg/detail/fim_arm__functions.h"
#include "genie_msgs/msg/detail/fim_arm__struct.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/header.h"
// Member `header`
#include "std_msgs/msg/detail/header__rosidl_typesupport_introspection_c.h"
// Member `fim_arm`
// Member `arm_err_code`
#include "rosidl_runtime_c/primitives_sequence_functions.h"

#ifdef __cplusplus
extern "C"
{
#endif

void genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__FimArm_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  genie_msgs__msg__FimArm__init(message_memory);
}

void genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__FimArm_fini_function(void * message_memory)
{
  genie_msgs__msg__FimArm__fini(message_memory);
}

size_t genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__size_function__FimArm__fim_arm(
  const void * untyped_member)
{
  const rosidl_runtime_c__uint8__Sequence * member =
    (const rosidl_runtime_c__uint8__Sequence *)(untyped_member);
  return member->size;
}

const void * genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__get_const_function__FimArm__fim_arm(
  const void * untyped_member, size_t index)
{
  const rosidl_runtime_c__uint8__Sequence * member =
    (const rosidl_runtime_c__uint8__Sequence *)(untyped_member);
  return &member->data[index];
}

void * genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__get_function__FimArm__fim_arm(
  void * untyped_member, size_t index)
{
  rosidl_runtime_c__uint8__Sequence * member =
    (rosidl_runtime_c__uint8__Sequence *)(untyped_member);
  return &member->data[index];
}

void genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__fetch_function__FimArm__fim_arm(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const uint8_t * item =
    ((const uint8_t *)
    genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__get_const_function__FimArm__fim_arm(untyped_member, index));
  uint8_t * value =
    (uint8_t *)(untyped_value);
  *value = *item;
}

void genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__assign_function__FimArm__fim_arm(
  void * untyped_member, size_t index, const void * untyped_value)
{
  uint8_t * item =
    ((uint8_t *)
    genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__get_function__FimArm__fim_arm(untyped_member, index));
  const uint8_t * value =
    (const uint8_t *)(untyped_value);
  *item = *value;
}

bool genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__resize_function__FimArm__fim_arm(
  void * untyped_member, size_t size)
{
  rosidl_runtime_c__uint8__Sequence * member =
    (rosidl_runtime_c__uint8__Sequence *)(untyped_member);
  rosidl_runtime_c__uint8__Sequence__fini(member);
  return rosidl_runtime_c__uint8__Sequence__init(member, size);
}

size_t genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__size_function__FimArm__arm_err_code(
  const void * untyped_member)
{
  const rosidl_runtime_c__uint16__Sequence * member =
    (const rosidl_runtime_c__uint16__Sequence *)(untyped_member);
  return member->size;
}

const void * genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__get_const_function__FimArm__arm_err_code(
  const void * untyped_member, size_t index)
{
  const rosidl_runtime_c__uint16__Sequence * member =
    (const rosidl_runtime_c__uint16__Sequence *)(untyped_member);
  return &member->data[index];
}

void * genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__get_function__FimArm__arm_err_code(
  void * untyped_member, size_t index)
{
  rosidl_runtime_c__uint16__Sequence * member =
    (rosidl_runtime_c__uint16__Sequence *)(untyped_member);
  return &member->data[index];
}

void genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__fetch_function__FimArm__arm_err_code(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const uint16_t * item =
    ((const uint16_t *)
    genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__get_const_function__FimArm__arm_err_code(untyped_member, index));
  uint16_t * value =
    (uint16_t *)(untyped_value);
  *value = *item;
}

void genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__assign_function__FimArm__arm_err_code(
  void * untyped_member, size_t index, const void * untyped_value)
{
  uint16_t * item =
    ((uint16_t *)
    genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__get_function__FimArm__arm_err_code(untyped_member, index));
  const uint16_t * value =
    (const uint16_t *)(untyped_value);
  *item = *value;
}

bool genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__resize_function__FimArm__arm_err_code(
  void * untyped_member, size_t size)
{
  rosidl_runtime_c__uint16__Sequence * member =
    (rosidl_runtime_c__uint16__Sequence *)(untyped_member);
  rosidl_runtime_c__uint16__Sequence__fini(member);
  return rosidl_runtime_c__uint16__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__FimArm_message_member_array[3] = {
  {
    "header",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__msg__FimArm, header),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "fim_arm",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT8,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__msg__FimArm, fim_arm),  // bytes offset in struct
    NULL,  // default value
    genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__size_function__FimArm__fim_arm,  // size() function pointer
    genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__get_const_function__FimArm__fim_arm,  // get_const(index) function pointer
    genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__get_function__FimArm__fim_arm,  // get(index) function pointer
    genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__fetch_function__FimArm__fim_arm,  // fetch(index, &value) function pointer
    genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__assign_function__FimArm__fim_arm,  // assign(index, value) function pointer
    genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__resize_function__FimArm__fim_arm  // resize(index) function pointer
  },
  {
    "arm_err_code",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT16,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__msg__FimArm, arm_err_code),  // bytes offset in struct
    NULL,  // default value
    genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__size_function__FimArm__arm_err_code,  // size() function pointer
    genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__get_const_function__FimArm__arm_err_code,  // get_const(index) function pointer
    genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__get_function__FimArm__arm_err_code,  // get(index) function pointer
    genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__fetch_function__FimArm__arm_err_code,  // fetch(index, &value) function pointer
    genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__assign_function__FimArm__arm_err_code,  // assign(index, value) function pointer
    genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__resize_function__FimArm__arm_err_code  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__FimArm_message_members = {
  "genie_msgs__msg",  // message namespace
  "FimArm",  // message name
  3,  // number of fields
  sizeof(genie_msgs__msg__FimArm),
  genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__FimArm_message_member_array,  // message members
  genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__FimArm_init_function,  // function to initialize message memory (memory has to be allocated)
  genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__FimArm_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__FimArm_message_type_support_handle = {
  0,
  &genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__FimArm_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_genie_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, genie_msgs, msg, FimArm)() {
  genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__FimArm_message_member_array[0].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, std_msgs, msg, Header)();
  if (!genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__FimArm_message_type_support_handle.typesupport_identifier) {
    genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__FimArm_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &genie_msgs__msg__FimArm__rosidl_typesupport_introspection_c__FimArm_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
