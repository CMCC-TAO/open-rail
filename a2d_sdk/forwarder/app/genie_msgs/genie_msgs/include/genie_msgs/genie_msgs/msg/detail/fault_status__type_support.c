// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from genie_msgs:msg/FaultStatus.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "genie_msgs/msg/detail/fault_status__rosidl_typesupport_introspection_c.h"
#include "genie_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "genie_msgs/msg/detail/fault_status__functions.h"
#include "genie_msgs/msg/detail/fault_status__struct.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/header.h"
// Member `header`
#include "std_msgs/msg/detail/header__rosidl_typesupport_introspection_c.h"
// Member `faults`
#include "genie_msgs/msg/fault_description.h"
// Member `faults`
#include "genie_msgs/msg/detail/fault_description__rosidl_typesupport_introspection_c.h"

#ifdef __cplusplus
extern "C"
{
#endif

void genie_msgs__msg__FaultStatus__rosidl_typesupport_introspection_c__FaultStatus_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  genie_msgs__msg__FaultStatus__init(message_memory);
}

void genie_msgs__msg__FaultStatus__rosidl_typesupport_introspection_c__FaultStatus_fini_function(void * message_memory)
{
  genie_msgs__msg__FaultStatus__fini(message_memory);
}

size_t genie_msgs__msg__FaultStatus__rosidl_typesupport_introspection_c__size_function__FaultStatus__faults(
  const void * untyped_member)
{
  const genie_msgs__msg__FaultDescription__Sequence * member =
    (const genie_msgs__msg__FaultDescription__Sequence *)(untyped_member);
  return member->size;
}

const void * genie_msgs__msg__FaultStatus__rosidl_typesupport_introspection_c__get_const_function__FaultStatus__faults(
  const void * untyped_member, size_t index)
{
  const genie_msgs__msg__FaultDescription__Sequence * member =
    (const genie_msgs__msg__FaultDescription__Sequence *)(untyped_member);
  return &member->data[index];
}

void * genie_msgs__msg__FaultStatus__rosidl_typesupport_introspection_c__get_function__FaultStatus__faults(
  void * untyped_member, size_t index)
{
  genie_msgs__msg__FaultDescription__Sequence * member =
    (genie_msgs__msg__FaultDescription__Sequence *)(untyped_member);
  return &member->data[index];
}

void genie_msgs__msg__FaultStatus__rosidl_typesupport_introspection_c__fetch_function__FaultStatus__faults(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const genie_msgs__msg__FaultDescription * item =
    ((const genie_msgs__msg__FaultDescription *)
    genie_msgs__msg__FaultStatus__rosidl_typesupport_introspection_c__get_const_function__FaultStatus__faults(untyped_member, index));
  genie_msgs__msg__FaultDescription * value =
    (genie_msgs__msg__FaultDescription *)(untyped_value);
  *value = *item;
}

void genie_msgs__msg__FaultStatus__rosidl_typesupport_introspection_c__assign_function__FaultStatus__faults(
  void * untyped_member, size_t index, const void * untyped_value)
{
  genie_msgs__msg__FaultDescription * item =
    ((genie_msgs__msg__FaultDescription *)
    genie_msgs__msg__FaultStatus__rosidl_typesupport_introspection_c__get_function__FaultStatus__faults(untyped_member, index));
  const genie_msgs__msg__FaultDescription * value =
    (const genie_msgs__msg__FaultDescription *)(untyped_value);
  *item = *value;
}

bool genie_msgs__msg__FaultStatus__rosidl_typesupport_introspection_c__resize_function__FaultStatus__faults(
  void * untyped_member, size_t size)
{
  genie_msgs__msg__FaultDescription__Sequence * member =
    (genie_msgs__msg__FaultDescription__Sequence *)(untyped_member);
  genie_msgs__msg__FaultDescription__Sequence__fini(member);
  return genie_msgs__msg__FaultDescription__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember genie_msgs__msg__FaultStatus__rosidl_typesupport_introspection_c__FaultStatus_message_member_array[2] = {
  {
    "header",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__msg__FaultStatus, header),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "faults",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__msg__FaultStatus, faults),  // bytes offset in struct
    NULL,  // default value
    genie_msgs__msg__FaultStatus__rosidl_typesupport_introspection_c__size_function__FaultStatus__faults,  // size() function pointer
    genie_msgs__msg__FaultStatus__rosidl_typesupport_introspection_c__get_const_function__FaultStatus__faults,  // get_const(index) function pointer
    genie_msgs__msg__FaultStatus__rosidl_typesupport_introspection_c__get_function__FaultStatus__faults,  // get(index) function pointer
    genie_msgs__msg__FaultStatus__rosidl_typesupport_introspection_c__fetch_function__FaultStatus__faults,  // fetch(index, &value) function pointer
    genie_msgs__msg__FaultStatus__rosidl_typesupport_introspection_c__assign_function__FaultStatus__faults,  // assign(index, value) function pointer
    genie_msgs__msg__FaultStatus__rosidl_typesupport_introspection_c__resize_function__FaultStatus__faults  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers genie_msgs__msg__FaultStatus__rosidl_typesupport_introspection_c__FaultStatus_message_members = {
  "genie_msgs__msg",  // message namespace
  "FaultStatus",  // message name
  2,  // number of fields
  sizeof(genie_msgs__msg__FaultStatus),
  genie_msgs__msg__FaultStatus__rosidl_typesupport_introspection_c__FaultStatus_message_member_array,  // message members
  genie_msgs__msg__FaultStatus__rosidl_typesupport_introspection_c__FaultStatus_init_function,  // function to initialize message memory (memory has to be allocated)
  genie_msgs__msg__FaultStatus__rosidl_typesupport_introspection_c__FaultStatus_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t genie_msgs__msg__FaultStatus__rosidl_typesupport_introspection_c__FaultStatus_message_type_support_handle = {
  0,
  &genie_msgs__msg__FaultStatus__rosidl_typesupport_introspection_c__FaultStatus_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_genie_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, genie_msgs, msg, FaultStatus)() {
  genie_msgs__msg__FaultStatus__rosidl_typesupport_introspection_c__FaultStatus_message_member_array[0].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, std_msgs, msg, Header)();
  genie_msgs__msg__FaultStatus__rosidl_typesupport_introspection_c__FaultStatus_message_member_array[1].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, genie_msgs, msg, FaultDescription)();
  if (!genie_msgs__msg__FaultStatus__rosidl_typesupport_introspection_c__FaultStatus_message_type_support_handle.typesupport_identifier) {
    genie_msgs__msg__FaultStatus__rosidl_typesupport_introspection_c__FaultStatus_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &genie_msgs__msg__FaultStatus__rosidl_typesupport_introspection_c__FaultStatus_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
