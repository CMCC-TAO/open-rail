// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from genie_msgs:msg/HeadState.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "genie_msgs/msg/detail/head_state__rosidl_typesupport_introspection_c.h"
#include "genie_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "genie_msgs/msg/detail/head_state__functions.h"
#include "genie_msgs/msg/detail/head_state__struct.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/header.h"
// Member `header`
#include "std_msgs/msg/detail/header__rosidl_typesupport_introspection_c.h"
// Member `motor_states`
#include "genie_msgs/msg/motor_state.h"
// Member `motor_states`
#include "genie_msgs/msg/detail/motor_state__rosidl_typesupport_introspection_c.h"
// Member `name`
#include "rosidl_runtime_c/string_functions.h"

#ifdef __cplusplus
extern "C"
{
#endif

void genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__HeadState_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  genie_msgs__msg__HeadState__init(message_memory);
}

void genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__HeadState_fini_function(void * message_memory)
{
  genie_msgs__msg__HeadState__fini(message_memory);
}

size_t genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__size_function__HeadState__motor_states(
  const void * untyped_member)
{
  const genie_msgs__msg__MotorState__Sequence * member =
    (const genie_msgs__msg__MotorState__Sequence *)(untyped_member);
  return member->size;
}

const void * genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__get_const_function__HeadState__motor_states(
  const void * untyped_member, size_t index)
{
  const genie_msgs__msg__MotorState__Sequence * member =
    (const genie_msgs__msg__MotorState__Sequence *)(untyped_member);
  return &member->data[index];
}

void * genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__get_function__HeadState__motor_states(
  void * untyped_member, size_t index)
{
  genie_msgs__msg__MotorState__Sequence * member =
    (genie_msgs__msg__MotorState__Sequence *)(untyped_member);
  return &member->data[index];
}

void genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__fetch_function__HeadState__motor_states(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const genie_msgs__msg__MotorState * item =
    ((const genie_msgs__msg__MotorState *)
    genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__get_const_function__HeadState__motor_states(untyped_member, index));
  genie_msgs__msg__MotorState * value =
    (genie_msgs__msg__MotorState *)(untyped_value);
  *value = *item;
}

void genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__assign_function__HeadState__motor_states(
  void * untyped_member, size_t index, const void * untyped_value)
{
  genie_msgs__msg__MotorState * item =
    ((genie_msgs__msg__MotorState *)
    genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__get_function__HeadState__motor_states(untyped_member, index));
  const genie_msgs__msg__MotorState * value =
    (const genie_msgs__msg__MotorState *)(untyped_value);
  *item = *value;
}

bool genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__resize_function__HeadState__motor_states(
  void * untyped_member, size_t size)
{
  genie_msgs__msg__MotorState__Sequence * member =
    (genie_msgs__msg__MotorState__Sequence *)(untyped_member);
  genie_msgs__msg__MotorState__Sequence__fini(member);
  return genie_msgs__msg__MotorState__Sequence__init(member, size);
}

size_t genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__size_function__HeadState__name(
  const void * untyped_member)
{
  const rosidl_runtime_c__String__Sequence * member =
    (const rosidl_runtime_c__String__Sequence *)(untyped_member);
  return member->size;
}

const void * genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__get_const_function__HeadState__name(
  const void * untyped_member, size_t index)
{
  const rosidl_runtime_c__String__Sequence * member =
    (const rosidl_runtime_c__String__Sequence *)(untyped_member);
  return &member->data[index];
}

void * genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__get_function__HeadState__name(
  void * untyped_member, size_t index)
{
  rosidl_runtime_c__String__Sequence * member =
    (rosidl_runtime_c__String__Sequence *)(untyped_member);
  return &member->data[index];
}

void genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__fetch_function__HeadState__name(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const rosidl_runtime_c__String * item =
    ((const rosidl_runtime_c__String *)
    genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__get_const_function__HeadState__name(untyped_member, index));
  rosidl_runtime_c__String * value =
    (rosidl_runtime_c__String *)(untyped_value);
  *value = *item;
}

void genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__assign_function__HeadState__name(
  void * untyped_member, size_t index, const void * untyped_value)
{
  rosidl_runtime_c__String * item =
    ((rosidl_runtime_c__String *)
    genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__get_function__HeadState__name(untyped_member, index));
  const rosidl_runtime_c__String * value =
    (const rosidl_runtime_c__String *)(untyped_value);
  *item = *value;
}

bool genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__resize_function__HeadState__name(
  void * untyped_member, size_t size)
{
  rosidl_runtime_c__String__Sequence * member =
    (rosidl_runtime_c__String__Sequence *)(untyped_member);
  rosidl_runtime_c__String__Sequence__fini(member);
  return rosidl_runtime_c__String__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__HeadState_message_member_array[3] = {
  {
    "header",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__msg__HeadState, header),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "motor_states",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__msg__HeadState, motor_states),  // bytes offset in struct
    NULL,  // default value
    genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__size_function__HeadState__motor_states,  // size() function pointer
    genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__get_const_function__HeadState__motor_states,  // get_const(index) function pointer
    genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__get_function__HeadState__motor_states,  // get(index) function pointer
    genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__fetch_function__HeadState__motor_states,  // fetch(index, &value) function pointer
    genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__assign_function__HeadState__motor_states,  // assign(index, value) function pointer
    genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__resize_function__HeadState__motor_states  // resize(index) function pointer
  },
  {
    "name",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__msg__HeadState, name),  // bytes offset in struct
    NULL,  // default value
    genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__size_function__HeadState__name,  // size() function pointer
    genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__get_const_function__HeadState__name,  // get_const(index) function pointer
    genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__get_function__HeadState__name,  // get(index) function pointer
    genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__fetch_function__HeadState__name,  // fetch(index, &value) function pointer
    genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__assign_function__HeadState__name,  // assign(index, value) function pointer
    genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__resize_function__HeadState__name  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__HeadState_message_members = {
  "genie_msgs__msg",  // message namespace
  "HeadState",  // message name
  3,  // number of fields
  sizeof(genie_msgs__msg__HeadState),
  genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__HeadState_message_member_array,  // message members
  genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__HeadState_init_function,  // function to initialize message memory (memory has to be allocated)
  genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__HeadState_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__HeadState_message_type_support_handle = {
  0,
  &genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__HeadState_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_genie_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, genie_msgs, msg, HeadState)() {
  genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__HeadState_message_member_array[0].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, std_msgs, msg, Header)();
  genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__HeadState_message_member_array[1].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, genie_msgs, msg, MotorState)();
  if (!genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__HeadState_message_type_support_handle.typesupport_identifier) {
    genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__HeadState_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &genie_msgs__msg__HeadState__rosidl_typesupport_introspection_c__HeadState_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
