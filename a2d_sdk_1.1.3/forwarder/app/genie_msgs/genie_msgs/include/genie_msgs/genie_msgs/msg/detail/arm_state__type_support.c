// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from genie_msgs:msg/ArmState.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "genie_msgs/msg/detail/arm_state__rosidl_typesupport_introspection_c.h"
#include "genie_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "genie_msgs/msg/detail/arm_state__functions.h"
#include "genie_msgs/msg/detail/arm_state__struct.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/header.h"
// Member `header`
#include "std_msgs/msg/detail/header__rosidl_typesupport_introspection_c.h"
// Member `motor_states`
#include "genie_msgs/msg/motor_state.h"
// Member `motor_states`
#include "genie_msgs/msg/detail/motor_state__rosidl_typesupport_introspection_c.h"
// Member `force_data`
#include "rosidl_runtime_c/primitives_sequence_functions.h"

#ifdef __cplusplus
extern "C"
{
#endif

void genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__ArmState_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  genie_msgs__msg__ArmState__init(message_memory);
}

void genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__ArmState_fini_function(void * message_memory)
{
  genie_msgs__msg__ArmState__fini(message_memory);
}

size_t genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__size_function__ArmState__motor_states(
  const void * untyped_member)
{
  const genie_msgs__msg__MotorState__Sequence * member =
    (const genie_msgs__msg__MotorState__Sequence *)(untyped_member);
  return member->size;
}

const void * genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__get_const_function__ArmState__motor_states(
  const void * untyped_member, size_t index)
{
  const genie_msgs__msg__MotorState__Sequence * member =
    (const genie_msgs__msg__MotorState__Sequence *)(untyped_member);
  return &member->data[index];
}

void * genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__get_function__ArmState__motor_states(
  void * untyped_member, size_t index)
{
  genie_msgs__msg__MotorState__Sequence * member =
    (genie_msgs__msg__MotorState__Sequence *)(untyped_member);
  return &member->data[index];
}

void genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__fetch_function__ArmState__motor_states(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const genie_msgs__msg__MotorState * item =
    ((const genie_msgs__msg__MotorState *)
    genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__get_const_function__ArmState__motor_states(untyped_member, index));
  genie_msgs__msg__MotorState * value =
    (genie_msgs__msg__MotorState *)(untyped_value);
  *value = *item;
}

void genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__assign_function__ArmState__motor_states(
  void * untyped_member, size_t index, const void * untyped_value)
{
  genie_msgs__msg__MotorState * item =
    ((genie_msgs__msg__MotorState *)
    genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__get_function__ArmState__motor_states(untyped_member, index));
  const genie_msgs__msg__MotorState * value =
    (const genie_msgs__msg__MotorState *)(untyped_value);
  *item = *value;
}

bool genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__resize_function__ArmState__motor_states(
  void * untyped_member, size_t size)
{
  genie_msgs__msg__MotorState__Sequence * member =
    (genie_msgs__msg__MotorState__Sequence *)(untyped_member);
  genie_msgs__msg__MotorState__Sequence__fini(member);
  return genie_msgs__msg__MotorState__Sequence__init(member, size);
}

size_t genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__size_function__ArmState__force_data(
  const void * untyped_member)
{
  const rosidl_runtime_c__double__Sequence * member =
    (const rosidl_runtime_c__double__Sequence *)(untyped_member);
  return member->size;
}

const void * genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__get_const_function__ArmState__force_data(
  const void * untyped_member, size_t index)
{
  const rosidl_runtime_c__double__Sequence * member =
    (const rosidl_runtime_c__double__Sequence *)(untyped_member);
  return &member->data[index];
}

void * genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__get_function__ArmState__force_data(
  void * untyped_member, size_t index)
{
  rosidl_runtime_c__double__Sequence * member =
    (rosidl_runtime_c__double__Sequence *)(untyped_member);
  return &member->data[index];
}

void genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__fetch_function__ArmState__force_data(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const double * item =
    ((const double *)
    genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__get_const_function__ArmState__force_data(untyped_member, index));
  double * value =
    (double *)(untyped_value);
  *value = *item;
}

void genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__assign_function__ArmState__force_data(
  void * untyped_member, size_t index, const void * untyped_value)
{
  double * item =
    ((double *)
    genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__get_function__ArmState__force_data(untyped_member, index));
  const double * value =
    (const double *)(untyped_value);
  *item = *value;
}

bool genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__resize_function__ArmState__force_data(
  void * untyped_member, size_t size)
{
  rosidl_runtime_c__double__Sequence * member =
    (rosidl_runtime_c__double__Sequence *)(untyped_member);
  rosidl_runtime_c__double__Sequence__fini(member);
  return rosidl_runtime_c__double__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__ArmState_message_member_array[7] = {
  {
    "header",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__msg__ArmState, header),  // bytes offset in struct
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
    offsetof(genie_msgs__msg__ArmState, motor_states),  // bytes offset in struct
    NULL,  // default value
    genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__size_function__ArmState__motor_states,  // size() function pointer
    genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__get_const_function__ArmState__motor_states,  // get_const(index) function pointer
    genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__get_function__ArmState__motor_states,  // get(index) function pointer
    genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__fetch_function__ArmState__motor_states,  // fetch(index, &value) function pointer
    genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__assign_function__ArmState__motor_states,  // assign(index, value) function pointer
    genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__resize_function__ArmState__motor_states  // resize(index) function pointer
  },
  {
    "force_data",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__msg__ArmState, force_data),  // bytes offset in struct
    NULL,  // default value
    genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__size_function__ArmState__force_data,  // size() function pointer
    genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__get_const_function__ArmState__force_data,  // get_const(index) function pointer
    genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__get_function__ArmState__force_data,  // get(index) function pointer
    genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__fetch_function__ArmState__force_data,  // fetch(index, &value) function pointer
    genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__assign_function__ArmState__force_data,  // assign(index, value) function pointer
    genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__resize_function__ArmState__force_data  // resize(index) function pointer
  },
  {
    "force_coordinate",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_INT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__msg__ArmState, force_coordinate),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "force_state",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_INT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__msg__ArmState, force_state),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "arm_state",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__msg__ArmState, arm_state),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "system_error",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_INT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__msg__ArmState, system_error),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__ArmState_message_members = {
  "genie_msgs__msg",  // message namespace
  "ArmState",  // message name
  7,  // number of fields
  sizeof(genie_msgs__msg__ArmState),
  genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__ArmState_message_member_array,  // message members
  genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__ArmState_init_function,  // function to initialize message memory (memory has to be allocated)
  genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__ArmState_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__ArmState_message_type_support_handle = {
  0,
  &genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__ArmState_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_genie_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, genie_msgs, msg, ArmState)() {
  genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__ArmState_message_member_array[0].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, std_msgs, msg, Header)();
  genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__ArmState_message_member_array[1].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, genie_msgs, msg, MotorState)();
  if (!genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__ArmState_message_type_support_handle.typesupport_identifier) {
    genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__ArmState_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &genie_msgs__msg__ArmState__rosidl_typesupport_introspection_c__ArmState_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
