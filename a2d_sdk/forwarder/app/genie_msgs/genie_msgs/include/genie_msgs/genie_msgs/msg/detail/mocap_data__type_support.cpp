// generated from rosidl_typesupport_introspection_cpp/resource/idl__type_support.cpp.em
// with input from genie_msgs:msg/MocapData.idl
// generated code does not contain a copyright notice

#include "array"
#include "cstddef"
#include "string"
#include "vector"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_interface/macros.h"
#include "genie_msgs/msg/detail/mocap_data__struct.hpp"
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

void MocapData_init_function(
  void * message_memory, rosidl_runtime_cpp::MessageInitialization _init)
{
  new (message_memory) genie_msgs::msg::MocapData(_init);
}

void MocapData_fini_function(void * message_memory)
{
  auto typed_message = static_cast<genie_msgs::msg::MocapData *>(message_memory);
  typed_message->~MocapData();
}

size_t size_function__MocapData__mocap_joint_states(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<genie_msgs::msg::MocapJointState> *>(untyped_member);
  return member->size();
}

const void * get_const_function__MocapData__mocap_joint_states(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<genie_msgs::msg::MocapJointState> *>(untyped_member);
  return &member[index];
}

void * get_function__MocapData__mocap_joint_states(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<genie_msgs::msg::MocapJointState> *>(untyped_member);
  return &member[index];
}

void fetch_function__MocapData__mocap_joint_states(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & item = *reinterpret_cast<const genie_msgs::msg::MocapJointState *>(
    get_const_function__MocapData__mocap_joint_states(untyped_member, index));
  auto & value = *reinterpret_cast<genie_msgs::msg::MocapJointState *>(untyped_value);
  value = item;
}

void assign_function__MocapData__mocap_joint_states(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & item = *reinterpret_cast<genie_msgs::msg::MocapJointState *>(
    get_function__MocapData__mocap_joint_states(untyped_member, index));
  const auto & value = *reinterpret_cast<const genie_msgs::msg::MocapJointState *>(untyped_value);
  item = value;
}

void resize_function__MocapData__mocap_joint_states(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<genie_msgs::msg::MocapJointState> *>(untyped_member);
  member->resize(size);
}

static const ::rosidl_typesupport_introspection_cpp::MessageMember MocapData_message_member_array[4] = {
  {
    "header",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<std_msgs::msg::Header>(),  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs::msg::MocapData, header),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "status",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_UINT32,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs::msg::MocapData, status),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "err_code",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_UINT32,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs::msg::MocapData, err_code),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "mocap_joint_states",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<genie_msgs::msg::MocapJointState>(),  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs::msg::MocapData, mocap_joint_states),  // bytes offset in struct
    nullptr,  // default value
    size_function__MocapData__mocap_joint_states,  // size() function pointer
    get_const_function__MocapData__mocap_joint_states,  // get_const(index) function pointer
    get_function__MocapData__mocap_joint_states,  // get(index) function pointer
    fetch_function__MocapData__mocap_joint_states,  // fetch(index, &value) function pointer
    assign_function__MocapData__mocap_joint_states,  // assign(index, value) function pointer
    resize_function__MocapData__mocap_joint_states  // resize(index) function pointer
  }
};

static const ::rosidl_typesupport_introspection_cpp::MessageMembers MocapData_message_members = {
  "genie_msgs::msg",  // message namespace
  "MocapData",  // message name
  4,  // number of fields
  sizeof(genie_msgs::msg::MocapData),
  MocapData_message_member_array,  // message members
  MocapData_init_function,  // function to initialize message memory (memory has to be allocated)
  MocapData_fini_function  // function to terminate message instance (will not free memory)
};

static const rosidl_message_type_support_t MocapData_message_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &MocapData_message_members,
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
get_message_type_support_handle<genie_msgs::msg::MocapData>()
{
  return &::genie_msgs::msg::rosidl_typesupport_introspection_cpp::MocapData_message_type_support_handle;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, genie_msgs, msg, MocapData)() {
  return &::genie_msgs::msg::rosidl_typesupport_introspection_cpp::MocapData_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif
