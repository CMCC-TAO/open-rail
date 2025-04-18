// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from genie_msgs:msg/MocapData.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "genie_msgs/msg/detail/mocap_data__rosidl_typesupport_introspection_c.h"
#include "genie_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "genie_msgs/msg/detail/mocap_data__functions.h"
#include "genie_msgs/msg/detail/mocap_data__struct.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/header.h"
// Member `header`
#include "std_msgs/msg/detail/header__rosidl_typesupport_introspection_c.h"
// Member `mocap_joint_states`
#include "genie_msgs/msg/mocap_joint_state.h"
// Member `mocap_joint_states`
#include "genie_msgs/msg/detail/mocap_joint_state__rosidl_typesupport_introspection_c.h"

#ifdef __cplusplus
extern "C"
{
#endif

void genie_msgs__msg__MocapData__rosidl_typesupport_introspection_c__MocapData_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  genie_msgs__msg__MocapData__init(message_memory);
}

void genie_msgs__msg__MocapData__rosidl_typesupport_introspection_c__MocapData_fini_function(void * message_memory)
{
  genie_msgs__msg__MocapData__fini(message_memory);
}

size_t genie_msgs__msg__MocapData__rosidl_typesupport_introspection_c__size_function__MocapData__mocap_joint_states(
  const void * untyped_member)
{
  const genie_msgs__msg__MocapJointState__Sequence * member =
    (const genie_msgs__msg__MocapJointState__Sequence *)(untyped_member);
  return member->size;
}

const void * genie_msgs__msg__MocapData__rosidl_typesupport_introspection_c__get_const_function__MocapData__mocap_joint_states(
  const void * untyped_member, size_t index)
{
  const genie_msgs__msg__MocapJointState__Sequence * member =
    (const genie_msgs__msg__MocapJointState__Sequence *)(untyped_member);
  return &member->data[index];
}

void * genie_msgs__msg__MocapData__rosidl_typesupport_introspection_c__get_function__MocapData__mocap_joint_states(
  void * untyped_member, size_t index)
{
  genie_msgs__msg__MocapJointState__Sequence * member =
    (genie_msgs__msg__MocapJointState__Sequence *)(untyped_member);
  return &member->data[index];
}

void genie_msgs__msg__MocapData__rosidl_typesupport_introspection_c__fetch_function__MocapData__mocap_joint_states(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const genie_msgs__msg__MocapJointState * item =
    ((const genie_msgs__msg__MocapJointState *)
    genie_msgs__msg__MocapData__rosidl_typesupport_introspection_c__get_const_function__MocapData__mocap_joint_states(untyped_member, index));
  genie_msgs__msg__MocapJointState * value =
    (genie_msgs__msg__MocapJointState *)(untyped_value);
  *value = *item;
}

void genie_msgs__msg__MocapData__rosidl_typesupport_introspection_c__assign_function__MocapData__mocap_joint_states(
  void * untyped_member, size_t index, const void * untyped_value)
{
  genie_msgs__msg__MocapJointState * item =
    ((genie_msgs__msg__MocapJointState *)
    genie_msgs__msg__MocapData__rosidl_typesupport_introspection_c__get_function__MocapData__mocap_joint_states(untyped_member, index));
  const genie_msgs__msg__MocapJointState * value =
    (const genie_msgs__msg__MocapJointState *)(untyped_value);
  *item = *value;
}

bool genie_msgs__msg__MocapData__rosidl_typesupport_introspection_c__resize_function__MocapData__mocap_joint_states(
  void * untyped_member, size_t size)
{
  genie_msgs__msg__MocapJointState__Sequence * member =
    (genie_msgs__msg__MocapJointState__Sequence *)(untyped_member);
  genie_msgs__msg__MocapJointState__Sequence__fini(member);
  return genie_msgs__msg__MocapJointState__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember genie_msgs__msg__MocapData__rosidl_typesupport_introspection_c__MocapData_message_member_array[4] = {
  {
    "header",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__msg__MocapData, header),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "status",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__msg__MocapData, status),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "err_code",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__msg__MocapData, err_code),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "mocap_joint_states",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__msg__MocapData, mocap_joint_states),  // bytes offset in struct
    NULL,  // default value
    genie_msgs__msg__MocapData__rosidl_typesupport_introspection_c__size_function__MocapData__mocap_joint_states,  // size() function pointer
    genie_msgs__msg__MocapData__rosidl_typesupport_introspection_c__get_const_function__MocapData__mocap_joint_states,  // get_const(index) function pointer
    genie_msgs__msg__MocapData__rosidl_typesupport_introspection_c__get_function__MocapData__mocap_joint_states,  // get(index) function pointer
    genie_msgs__msg__MocapData__rosidl_typesupport_introspection_c__fetch_function__MocapData__mocap_joint_states,  // fetch(index, &value) function pointer
    genie_msgs__msg__MocapData__rosidl_typesupport_introspection_c__assign_function__MocapData__mocap_joint_states,  // assign(index, value) function pointer
    genie_msgs__msg__MocapData__rosidl_typesupport_introspection_c__resize_function__MocapData__mocap_joint_states  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers genie_msgs__msg__MocapData__rosidl_typesupport_introspection_c__MocapData_message_members = {
  "genie_msgs__msg",  // message namespace
  "MocapData",  // message name
  4,  // number of fields
  sizeof(genie_msgs__msg__MocapData),
  genie_msgs__msg__MocapData__rosidl_typesupport_introspection_c__MocapData_message_member_array,  // message members
  genie_msgs__msg__MocapData__rosidl_typesupport_introspection_c__MocapData_init_function,  // function to initialize message memory (memory has to be allocated)
  genie_msgs__msg__MocapData__rosidl_typesupport_introspection_c__MocapData_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t genie_msgs__msg__MocapData__rosidl_typesupport_introspection_c__MocapData_message_type_support_handle = {
  0,
  &genie_msgs__msg__MocapData__rosidl_typesupport_introspection_c__MocapData_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_genie_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, genie_msgs, msg, MocapData)() {
  genie_msgs__msg__MocapData__rosidl_typesupport_introspection_c__MocapData_message_member_array[0].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, std_msgs, msg, Header)();
  genie_msgs__msg__MocapData__rosidl_typesupport_introspection_c__MocapData_message_member_array[3].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, genie_msgs, msg, MocapJointState)();
  if (!genie_msgs__msg__MocapData__rosidl_typesupport_introspection_c__MocapData_message_type_support_handle.typesupport_identifier) {
    genie_msgs__msg__MocapData__rosidl_typesupport_introspection_c__MocapData_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &genie_msgs__msg__MocapData__rosidl_typesupport_introspection_c__MocapData_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
