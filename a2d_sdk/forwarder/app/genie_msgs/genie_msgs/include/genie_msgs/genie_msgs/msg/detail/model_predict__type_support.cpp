// generated from rosidl_typesupport_introspection_cpp/resource/idl__type_support.cpp.em
// with input from genie_msgs:msg/ModelPredict.idl
// generated code does not contain a copyright notice

#include "array"
#include "cstddef"
#include "string"
#include "vector"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_interface/macros.h"
#include "genie_msgs/msg/detail/model_predict__struct.hpp"
#include "rosidl_typesupport_introspection_cpp/field_types.hpp"
#include "rosidl_typesupport_introspection_cpp/identifier.hpp"
#include "rosidl_typesupport_introspection_cpp/message_introspection.hpp"
#include "rosidl_typesupport_introspection_cpp/message_type_support_decl.hpp"
#include "rosidl_typesupport_introspection_cpp/visibility_control.h"

namespace genie_msgs
{

namespace msg
{

namespace rosidl_typesupport_introspection_cpp
{

void ModelPredict_init_function(
  void * message_memory, rosidl_runtime_cpp::MessageInitialization _init)
{
  new (message_memory) genie_msgs::msg::ModelPredict(_init);
}

void ModelPredict_fini_function(void * message_memory)
{
  auto typed_message = static_cast<genie_msgs::msg::ModelPredict *>(message_memory);
  typed_message->~ModelPredict();
}

size_t size_function__ModelPredict__body_joint_names(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<std::string> *>(untyped_member);
  return member->size();
}

const void * get_const_function__ModelPredict__body_joint_names(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<std::string> *>(untyped_member);
  return &member[index];
}

void * get_function__ModelPredict__body_joint_names(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<std::string> *>(untyped_member);
  return &member[index];
}

void fetch_function__ModelPredict__body_joint_names(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & item = *reinterpret_cast<const std::string *>(
    get_const_function__ModelPredict__body_joint_names(untyped_member, index));
  auto & value = *reinterpret_cast<std::string *>(untyped_value);
  value = item;
}

void assign_function__ModelPredict__body_joint_names(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & item = *reinterpret_cast<std::string *>(
    get_function__ModelPredict__body_joint_names(untyped_member, index));
  const auto & value = *reinterpret_cast<const std::string *>(untyped_value);
  item = value;
}

void resize_function__ModelPredict__body_joint_names(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<std::string> *>(untyped_member);
  member->resize(size);
}

size_t size_function__ModelPredict__body_joint_positions(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<double> *>(untyped_member);
  return member->size();
}

const void * get_const_function__ModelPredict__body_joint_positions(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<double> *>(untyped_member);
  return &member[index];
}

void * get_function__ModelPredict__body_joint_positions(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<double> *>(untyped_member);
  return &member[index];
}

void fetch_function__ModelPredict__body_joint_positions(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & item = *reinterpret_cast<const double *>(
    get_const_function__ModelPredict__body_joint_positions(untyped_member, index));
  auto & value = *reinterpret_cast<double *>(untyped_value);
  value = item;
}

void assign_function__ModelPredict__body_joint_positions(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & item = *reinterpret_cast<double *>(
    get_function__ModelPredict__body_joint_positions(untyped_member, index));
  const auto & value = *reinterpret_cast<const double *>(untyped_value);
  item = value;
}

void resize_function__ModelPredict__body_joint_positions(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<double> *>(untyped_member);
  member->resize(size);
}

size_t size_function__ModelPredict__target_poses(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<geometry_msgs::msg::Pose> *>(untyped_member);
  return member->size();
}

const void * get_const_function__ModelPredict__target_poses(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<geometry_msgs::msg::Pose> *>(untyped_member);
  return &member[index];
}

void * get_function__ModelPredict__target_poses(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<geometry_msgs::msg::Pose> *>(untyped_member);
  return &member[index];
}

void fetch_function__ModelPredict__target_poses(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & item = *reinterpret_cast<const geometry_msgs::msg::Pose *>(
    get_const_function__ModelPredict__target_poses(untyped_member, index));
  auto & value = *reinterpret_cast<geometry_msgs::msg::Pose *>(untyped_value);
  value = item;
}

void assign_function__ModelPredict__target_poses(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & item = *reinterpret_cast<geometry_msgs::msg::Pose *>(
    get_function__ModelPredict__target_poses(untyped_member, index));
  const auto & value = *reinterpret_cast<const geometry_msgs::msg::Pose *>(untyped_value);
  item = value;
}

void resize_function__ModelPredict__target_poses(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<geometry_msgs::msg::Pose> *>(untyped_member);
  member->resize(size);
}

size_t size_function__ModelPredict__target_joint_states(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<sensor_msgs::msg::JointState> *>(untyped_member);
  return member->size();
}

const void * get_const_function__ModelPredict__target_joint_states(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<sensor_msgs::msg::JointState> *>(untyped_member);
  return &member[index];
}

void * get_function__ModelPredict__target_joint_states(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<sensor_msgs::msg::JointState> *>(untyped_member);
  return &member[index];
}

void fetch_function__ModelPredict__target_joint_states(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & item = *reinterpret_cast<const sensor_msgs::msg::JointState *>(
    get_const_function__ModelPredict__target_joint_states(untyped_member, index));
  auto & value = *reinterpret_cast<sensor_msgs::msg::JointState *>(untyped_value);
  value = item;
}

void assign_function__ModelPredict__target_joint_states(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & item = *reinterpret_cast<sensor_msgs::msg::JointState *>(
    get_function__ModelPredict__target_joint_states(untyped_member, index));
  const auto & value = *reinterpret_cast<const sensor_msgs::msg::JointState *>(untyped_value);
  item = value;
}

void resize_function__ModelPredict__target_joint_states(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<sensor_msgs::msg::JointState> *>(untyped_member);
  member->resize(size);
}

static const ::rosidl_typesupport_introspection_cpp::MessageMember ModelPredict_message_member_array[8] = {
  {
    "header",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<std_msgs::msg::Header>(),  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs::msg::ModelPredict, header),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "body_joint_names",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs::msg::ModelPredict, body_joint_names),  // bytes offset in struct
    nullptr,  // default value
    size_function__ModelPredict__body_joint_names,  // size() function pointer
    get_const_function__ModelPredict__body_joint_names,  // get_const(index) function pointer
    get_function__ModelPredict__body_joint_names,  // get(index) function pointer
    fetch_function__ModelPredict__body_joint_names,  // fetch(index, &value) function pointer
    assign_function__ModelPredict__body_joint_names,  // assign(index, value) function pointer
    resize_function__ModelPredict__body_joint_names  // resize(index) function pointer
  },
  {
    "body_joint_positions",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs::msg::ModelPredict, body_joint_positions),  // bytes offset in struct
    nullptr,  // default value
    size_function__ModelPredict__body_joint_positions,  // size() function pointer
    get_const_function__ModelPredict__body_joint_positions,  // get_const(index) function pointer
    get_function__ModelPredict__body_joint_positions,  // get(index) function pointer
    fetch_function__ModelPredict__body_joint_positions,  // fetch(index, &value) function pointer
    assign_function__ModelPredict__body_joint_positions,  // assign(index, value) function pointer
    resize_function__ModelPredict__body_joint_positions  // resize(index) function pointer
  },
  {
    "model_output_type",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_UINT8,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs::msg::ModelPredict, model_output_type),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "target_poses",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<geometry_msgs::msg::Pose>(),  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs::msg::ModelPredict, target_poses),  // bytes offset in struct
    nullptr,  // default value
    size_function__ModelPredict__target_poses,  // size() function pointer
    get_const_function__ModelPredict__target_poses,  // get_const(index) function pointer
    get_function__ModelPredict__target_poses,  // get(index) function pointer
    fetch_function__ModelPredict__target_poses,  // fetch(index, &value) function pointer
    assign_function__ModelPredict__target_poses,  // assign(index, value) function pointer
    resize_function__ModelPredict__target_poses  // resize(index) function pointer
  },
  {
    "target_joint_states",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<sensor_msgs::msg::JointState>(),  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs::msg::ModelPredict, target_joint_states),  // bytes offset in struct
    nullptr,  // default value
    size_function__ModelPredict__target_joint_states,  // size() function pointer
    get_const_function__ModelPredict__target_joint_states,  // get_const(index) function pointer
    get_function__ModelPredict__target_joint_states,  // get(index) function pointer
    fetch_function__ModelPredict__target_joint_states,  // fetch(index, &value) function pointer
    assign_function__ModelPredict__target_joint_states,  // assign(index, value) function pointer
    resize_function__ModelPredict__target_joint_states  // resize(index) function pointer
  },
  {
    "model_sleep_time",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs::msg::ModelPredict, model_sleep_time),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "trajectory_reference_time",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs::msg::ModelPredict, trajectory_reference_time),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  }
};

static const ::rosidl_typesupport_introspection_cpp::MessageMembers ModelPredict_message_members = {
  "genie_msgs::msg",  // message namespace
  "ModelPredict",  // message name
  8,  // number of fields
  sizeof(genie_msgs::msg::ModelPredict),
  ModelPredict_message_member_array,  // message members
  ModelPredict_init_function,  // function to initialize message memory (memory has to be allocated)
  ModelPredict_fini_function  // function to terminate message instance (will not free memory)
};

static const rosidl_message_type_support_t ModelPredict_message_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &ModelPredict_message_members,
  get_message_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_introspection_cpp

}  // namespace msg

}  // namespace genie_msgs


namespace rosidl_typesupport_introspection_cpp
{

template<>
ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<genie_msgs::msg::ModelPredict>()
{
  return &::genie_msgs::msg::rosidl_typesupport_introspection_cpp::ModelPredict_message_type_support_handle;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, genie_msgs, msg, ModelPredict)() {
  return &::genie_msgs::msg::rosidl_typesupport_introspection_cpp::ModelPredict_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif
