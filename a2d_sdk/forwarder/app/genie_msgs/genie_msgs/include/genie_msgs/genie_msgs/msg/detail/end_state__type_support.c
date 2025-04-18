// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from genie_msgs:msg/EndState.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "genie_msgs/msg/detail/end_state__rosidl_typesupport_introspection_c.h"
#include "genie_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "genie_msgs/msg/detail/end_state__functions.h"
#include "genie_msgs/msg/detail/end_state__struct.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/header.h"
// Member `header`
#include "std_msgs/msg/detail/header__rosidl_typesupport_introspection_c.h"
// Member `end_state`
#include "genie_msgs/msg/motor_state.h"
// Member `end_state`
#include "genie_msgs/msg/detail/motor_state__rosidl_typesupport_introspection_c.h"

#ifdef __cplusplus
extern "C"
{
#endif

void genie_msgs__msg__EndState__rosidl_typesupport_introspection_c__EndState_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  genie_msgs__msg__EndState__init(message_memory);
}

void genie_msgs__msg__EndState__rosidl_typesupport_introspection_c__EndState_fini_function(void * message_memory)
{
  genie_msgs__msg__EndState__fini(message_memory);
}

size_t genie_msgs__msg__EndState__rosidl_typesupport_introspection_c__size_function__EndState__end_state(
  const void * untyped_member)
{
  const genie_msgs__msg__MotorState__Sequence * member =
    (const genie_msgs__msg__MotorState__Sequence *)(untyped_member);
  return member->size;
}

const void * genie_msgs__msg__EndState__rosidl_typesupport_introspection_c__get_const_function__EndState__end_state(
  const void * untyped_member, size_t index)
{
  const genie_msgs__msg__MotorState__Sequence * member =
    (const genie_msgs__msg__MotorState__Sequence *)(untyped_member);
  return &member->data[index];
}

void * genie_msgs__msg__EndState__rosidl_typesupport_introspection_c__get_function__EndState__end_state(
  void * untyped_member, size_t index)
{
  genie_msgs__msg__MotorState__Sequence * member =
    (genie_msgs__msg__MotorState__Sequence *)(untyped_member);
  return &member->data[index];
}

void genie_msgs__msg__EndState__rosidl_typesupport_introspection_c__fetch_function__EndState__end_state(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const genie_msgs__msg__MotorState * item =
    ((const genie_msgs__msg__MotorState *)
    genie_msgs__msg__EndState__rosidl_typesupport_introspection_c__get_const_function__EndState__end_state(untyped_member, index));
  genie_msgs__msg__MotorState * value =
    (genie_msgs__msg__MotorState *)(untyped_value);
  *value = *item;
}

void genie_msgs__msg__EndState__rosidl_typesupport_introspection_c__assign_function__EndState__end_state(
  void * untyped_member, size_t index, const void * untyped_value)
{
  genie_msgs__msg__MotorState * item =
    ((genie_msgs__msg__MotorState *)
    genie_msgs__msg__EndState__rosidl_typesupport_introspection_c__get_function__EndState__end_state(untyped_member, index));
  const genie_msgs__msg__MotorState * value =
    (const genie_msgs__msg__MotorState *)(untyped_value);
  *item = *value;
}

bool genie_msgs__msg__EndState__rosidl_typesupport_introspection_c__resize_function__EndState__end_state(
  void * untyped_member, size_t size)
{
  genie_msgs__msg__MotorState__Sequence * member =
    (genie_msgs__msg__MotorState__Sequence *)(untyped_member);
  genie_msgs__msg__MotorState__Sequence__fini(member);
  return genie_msgs__msg__MotorState__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember genie_msgs__msg__EndState__rosidl_typesupport_introspection_c__EndState_message_member_array[3] = {
  {
    "header",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__msg__EndState, header),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "controlled",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_BOOLEAN,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__msg__EndState, controlled),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "end_state",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__msg__EndState, end_state),  // bytes offset in struct
    NULL,  // default value
    genie_msgs__msg__EndState__rosidl_typesupport_introspection_c__size_function__EndState__end_state,  // size() function pointer
    genie_msgs__msg__EndState__rosidl_typesupport_introspection_c__get_const_function__EndState__end_state,  // get_const(index) function pointer
    genie_msgs__msg__EndState__rosidl_typesupport_introspection_c__get_function__EndState__end_state,  // get(index) function pointer
    genie_msgs__msg__EndState__rosidl_typesupport_introspection_c__fetch_function__EndState__end_state,  // fetch(index, &value) function pointer
    genie_msgs__msg__EndState__rosidl_typesupport_introspection_c__assign_function__EndState__end_state,  // assign(index, value) function pointer
    genie_msgs__msg__EndState__rosidl_typesupport_introspection_c__resize_function__EndState__end_state  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers genie_msgs__msg__EndState__rosidl_typesupport_introspection_c__EndState_message_members = {
  "genie_msgs__msg",  // message namespace
  "EndState",  // message name
  3,  // number of fields
  sizeof(genie_msgs__msg__EndState),
  genie_msgs__msg__EndState__rosidl_typesupport_introspection_c__EndState_message_member_array,  // message members
  genie_msgs__msg__EndState__rosidl_typesupport_introspection_c__EndState_init_function,  // function to initialize message memory (memory has to be allocated)
  genie_msgs__msg__EndState__rosidl_typesupport_introspection_c__EndState_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t genie_msgs__msg__EndState__rosidl_typesupport_introspection_c__EndState_message_type_support_handle = {
  0,
  &genie_msgs__msg__EndState__rosidl_typesupport_introspection_c__EndState_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_genie_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, genie_msgs, msg, EndState)() {
  genie_msgs__msg__EndState__rosidl_typesupport_introspection_c__EndState_message_member_array[0].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, std_msgs, msg, Header)();
  genie_msgs__msg__EndState__rosidl_typesupport_introspection_c__EndState_message_member_array[2].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, genie_msgs, msg, MotorState)();
  if (!genie_msgs__msg__EndState__rosidl_typesupport_introspection_c__EndState_message_type_support_handle.typesupport_identifier) {
    genie_msgs__msg__EndState__rosidl_typesupport_introspection_c__EndState_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &genie_msgs__msg__EndState__rosidl_typesupport_introspection_c__EndState_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
