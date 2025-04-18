// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from genie_msgs:msg/ModelPredict.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "genie_msgs/msg/detail/model_predict__rosidl_typesupport_introspection_c.h"
#include "genie_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "genie_msgs/msg/detail/model_predict__functions.h"
#include "genie_msgs/msg/detail/model_predict__struct.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/header.h"
// Member `header`
#include "std_msgs/msg/detail/header__rosidl_typesupport_introspection_c.h"
// Member `body_joint_names`
#include "rosidl_runtime_c/string_functions.h"
// Member `body_joint_positions`
#include "rosidl_runtime_c/primitives_sequence_functions.h"
// Member `target_poses`
#include "geometry_msgs/msg/pose.h"
// Member `target_poses`
#include "geometry_msgs/msg/detail/pose__rosidl_typesupport_introspection_c.h"
// Member `target_joint_states`
#include "sensor_msgs/msg/joint_state.h"
// Member `target_joint_states`
#include "sensor_msgs/msg/detail/joint_state__rosidl_typesupport_introspection_c.h"

#ifdef __cplusplus
extern "C"
{
#endif

void genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__ModelPredict_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  genie_msgs__msg__ModelPredict__init(message_memory);
}

void genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__ModelPredict_fini_function(void * message_memory)
{
  genie_msgs__msg__ModelPredict__fini(message_memory);
}

size_t genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__size_function__ModelPredict__body_joint_names(
  const void * untyped_member)
{
  const rosidl_runtime_c__String__Sequence * member =
    (const rosidl_runtime_c__String__Sequence *)(untyped_member);
  return member->size;
}

const void * genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__get_const_function__ModelPredict__body_joint_names(
  const void * untyped_member, size_t index)
{
  const rosidl_runtime_c__String__Sequence * member =
    (const rosidl_runtime_c__String__Sequence *)(untyped_member);
  return &member->data[index];
}

void * genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__get_function__ModelPredict__body_joint_names(
  void * untyped_member, size_t index)
{
  rosidl_runtime_c__String__Sequence * member =
    (rosidl_runtime_c__String__Sequence *)(untyped_member);
  return &member->data[index];
}

void genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__fetch_function__ModelPredict__body_joint_names(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const rosidl_runtime_c__String * item =
    ((const rosidl_runtime_c__String *)
    genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__get_const_function__ModelPredict__body_joint_names(untyped_member, index));
  rosidl_runtime_c__String * value =
    (rosidl_runtime_c__String *)(untyped_value);
  *value = *item;
}

void genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__assign_function__ModelPredict__body_joint_names(
  void * untyped_member, size_t index, const void * untyped_value)
{
  rosidl_runtime_c__String * item =
    ((rosidl_runtime_c__String *)
    genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__get_function__ModelPredict__body_joint_names(untyped_member, index));
  const rosidl_runtime_c__String * value =
    (const rosidl_runtime_c__String *)(untyped_value);
  *item = *value;
}

bool genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__resize_function__ModelPredict__body_joint_names(
  void * untyped_member, size_t size)
{
  rosidl_runtime_c__String__Sequence * member =
    (rosidl_runtime_c__String__Sequence *)(untyped_member);
  rosidl_runtime_c__String__Sequence__fini(member);
  return rosidl_runtime_c__String__Sequence__init(member, size);
}

size_t genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__size_function__ModelPredict__body_joint_positions(
  const void * untyped_member)
{
  const rosidl_runtime_c__double__Sequence * member =
    (const rosidl_runtime_c__double__Sequence *)(untyped_member);
  return member->size;
}

const void * genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__get_const_function__ModelPredict__body_joint_positions(
  const void * untyped_member, size_t index)
{
  const rosidl_runtime_c__double__Sequence * member =
    (const rosidl_runtime_c__double__Sequence *)(untyped_member);
  return &member->data[index];
}

void * genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__get_function__ModelPredict__body_joint_positions(
  void * untyped_member, size_t index)
{
  rosidl_runtime_c__double__Sequence * member =
    (rosidl_runtime_c__double__Sequence *)(untyped_member);
  return &member->data[index];
}

void genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__fetch_function__ModelPredict__body_joint_positions(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const double * item =
    ((const double *)
    genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__get_const_function__ModelPredict__body_joint_positions(untyped_member, index));
  double * value =
    (double *)(untyped_value);
  *value = *item;
}

void genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__assign_function__ModelPredict__body_joint_positions(
  void * untyped_member, size_t index, const void * untyped_value)
{
  double * item =
    ((double *)
    genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__get_function__ModelPredict__body_joint_positions(untyped_member, index));
  const double * value =
    (const double *)(untyped_value);
  *item = *value;
}

bool genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__resize_function__ModelPredict__body_joint_positions(
  void * untyped_member, size_t size)
{
  rosidl_runtime_c__double__Sequence * member =
    (rosidl_runtime_c__double__Sequence *)(untyped_member);
  rosidl_runtime_c__double__Sequence__fini(member);
  return rosidl_runtime_c__double__Sequence__init(member, size);
}

size_t genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__size_function__ModelPredict__target_poses(
  const void * untyped_member)
{
  const geometry_msgs__msg__Pose__Sequence * member =
    (const geometry_msgs__msg__Pose__Sequence *)(untyped_member);
  return member->size;
}

const void * genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__get_const_function__ModelPredict__target_poses(
  const void * untyped_member, size_t index)
{
  const geometry_msgs__msg__Pose__Sequence * member =
    (const geometry_msgs__msg__Pose__Sequence *)(untyped_member);
  return &member->data[index];
}

void * genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__get_function__ModelPredict__target_poses(
  void * untyped_member, size_t index)
{
  geometry_msgs__msg__Pose__Sequence * member =
    (geometry_msgs__msg__Pose__Sequence *)(untyped_member);
  return &member->data[index];
}

void genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__fetch_function__ModelPredict__target_poses(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const geometry_msgs__msg__Pose * item =
    ((const geometry_msgs__msg__Pose *)
    genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__get_const_function__ModelPredict__target_poses(untyped_member, index));
  geometry_msgs__msg__Pose * value =
    (geometry_msgs__msg__Pose *)(untyped_value);
  *value = *item;
}

void genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__assign_function__ModelPredict__target_poses(
  void * untyped_member, size_t index, const void * untyped_value)
{
  geometry_msgs__msg__Pose * item =
    ((geometry_msgs__msg__Pose *)
    genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__get_function__ModelPredict__target_poses(untyped_member, index));
  const geometry_msgs__msg__Pose * value =
    (const geometry_msgs__msg__Pose *)(untyped_value);
  *item = *value;
}

bool genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__resize_function__ModelPredict__target_poses(
  void * untyped_member, size_t size)
{
  geometry_msgs__msg__Pose__Sequence * member =
    (geometry_msgs__msg__Pose__Sequence *)(untyped_member);
  geometry_msgs__msg__Pose__Sequence__fini(member);
  return geometry_msgs__msg__Pose__Sequence__init(member, size);
}

size_t genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__size_function__ModelPredict__target_joint_states(
  const void * untyped_member)
{
  const sensor_msgs__msg__JointState__Sequence * member =
    (const sensor_msgs__msg__JointState__Sequence *)(untyped_member);
  return member->size;
}

const void * genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__get_const_function__ModelPredict__target_joint_states(
  const void * untyped_member, size_t index)
{
  const sensor_msgs__msg__JointState__Sequence * member =
    (const sensor_msgs__msg__JointState__Sequence *)(untyped_member);
  return &member->data[index];
}

void * genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__get_function__ModelPredict__target_joint_states(
  void * untyped_member, size_t index)
{
  sensor_msgs__msg__JointState__Sequence * member =
    (sensor_msgs__msg__JointState__Sequence *)(untyped_member);
  return &member->data[index];
}

void genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__fetch_function__ModelPredict__target_joint_states(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const sensor_msgs__msg__JointState * item =
    ((const sensor_msgs__msg__JointState *)
    genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__get_const_function__ModelPredict__target_joint_states(untyped_member, index));
  sensor_msgs__msg__JointState * value =
    (sensor_msgs__msg__JointState *)(untyped_value);
  *value = *item;
}

void genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__assign_function__ModelPredict__target_joint_states(
  void * untyped_member, size_t index, const void * untyped_value)
{
  sensor_msgs__msg__JointState * item =
    ((sensor_msgs__msg__JointState *)
    genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__get_function__ModelPredict__target_joint_states(untyped_member, index));
  const sensor_msgs__msg__JointState * value =
    (const sensor_msgs__msg__JointState *)(untyped_value);
  *item = *value;
}

bool genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__resize_function__ModelPredict__target_joint_states(
  void * untyped_member, size_t size)
{
  sensor_msgs__msg__JointState__Sequence * member =
    (sensor_msgs__msg__JointState__Sequence *)(untyped_member);
  sensor_msgs__msg__JointState__Sequence__fini(member);
  return sensor_msgs__msg__JointState__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__ModelPredict_message_member_array[8] = {
  {
    "header",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__msg__ModelPredict, header),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "body_joint_names",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__msg__ModelPredict, body_joint_names),  // bytes offset in struct
    NULL,  // default value
    genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__size_function__ModelPredict__body_joint_names,  // size() function pointer
    genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__get_const_function__ModelPredict__body_joint_names,  // get_const(index) function pointer
    genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__get_function__ModelPredict__body_joint_names,  // get(index) function pointer
    genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__fetch_function__ModelPredict__body_joint_names,  // fetch(index, &value) function pointer
    genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__assign_function__ModelPredict__body_joint_names,  // assign(index, value) function pointer
    genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__resize_function__ModelPredict__body_joint_names  // resize(index) function pointer
  },
  {
    "body_joint_positions",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__msg__ModelPredict, body_joint_positions),  // bytes offset in struct
    NULL,  // default value
    genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__size_function__ModelPredict__body_joint_positions,  // size() function pointer
    genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__get_const_function__ModelPredict__body_joint_positions,  // get_const(index) function pointer
    genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__get_function__ModelPredict__body_joint_positions,  // get(index) function pointer
    genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__fetch_function__ModelPredict__body_joint_positions,  // fetch(index, &value) function pointer
    genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__assign_function__ModelPredict__body_joint_positions,  // assign(index, value) function pointer
    genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__resize_function__ModelPredict__body_joint_positions  // resize(index) function pointer
  },
  {
    "model_output_type",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT8,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__msg__ModelPredict, model_output_type),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "target_poses",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__msg__ModelPredict, target_poses),  // bytes offset in struct
    NULL,  // default value
    genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__size_function__ModelPredict__target_poses,  // size() function pointer
    genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__get_const_function__ModelPredict__target_poses,  // get_const(index) function pointer
    genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__get_function__ModelPredict__target_poses,  // get(index) function pointer
    genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__fetch_function__ModelPredict__target_poses,  // fetch(index, &value) function pointer
    genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__assign_function__ModelPredict__target_poses,  // assign(index, value) function pointer
    genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__resize_function__ModelPredict__target_poses  // resize(index) function pointer
  },
  {
    "target_joint_states",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__msg__ModelPredict, target_joint_states),  // bytes offset in struct
    NULL,  // default value
    genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__size_function__ModelPredict__target_joint_states,  // size() function pointer
    genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__get_const_function__ModelPredict__target_joint_states,  // get_const(index) function pointer
    genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__get_function__ModelPredict__target_joint_states,  // get(index) function pointer
    genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__fetch_function__ModelPredict__target_joint_states,  // fetch(index, &value) function pointer
    genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__assign_function__ModelPredict__target_joint_states,  // assign(index, value) function pointer
    genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__resize_function__ModelPredict__target_joint_states  // resize(index) function pointer
  },
  {
    "model_sleep_time",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__msg__ModelPredict, model_sleep_time),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "trajectory_reference_time",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs__msg__ModelPredict, trajectory_reference_time),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__ModelPredict_message_members = {
  "genie_msgs__msg",  // message namespace
  "ModelPredict",  // message name
  8,  // number of fields
  sizeof(genie_msgs__msg__ModelPredict),
  genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__ModelPredict_message_member_array,  // message members
  genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__ModelPredict_init_function,  // function to initialize message memory (memory has to be allocated)
  genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__ModelPredict_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__ModelPredict_message_type_support_handle = {
  0,
  &genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__ModelPredict_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_genie_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, genie_msgs, msg, ModelPredict)() {
  genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__ModelPredict_message_member_array[0].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, std_msgs, msg, Header)();
  genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__ModelPredict_message_member_array[4].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, geometry_msgs, msg, Pose)();
  genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__ModelPredict_message_member_array[5].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, sensor_msgs, msg, JointState)();
  if (!genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__ModelPredict_message_type_support_handle.typesupport_identifier) {
    genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__ModelPredict_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &genie_msgs__msg__ModelPredict__rosidl_typesupport_introspection_c__ModelPredict_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
