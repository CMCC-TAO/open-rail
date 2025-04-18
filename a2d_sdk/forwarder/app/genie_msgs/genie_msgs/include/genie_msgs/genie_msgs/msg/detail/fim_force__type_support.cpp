// generated from rosidl_typesupport_introspection_cpp/resource/idl__type_support.cpp.em
// with input from genie_msgs:msg/FimForce.idl
// generated code does not contain a copyright notice

#include "array"
#include "cstddef"
#include "string"
#include "vector"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_interface/macros.h"
#include "genie_msgs/msg/detail/fim_force__struct.hpp"
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

void FimForce_init_function(
  void * message_memory, rosidl_runtime_cpp::MessageInitialization _init)
{
  new (message_memory) genie_msgs::msg::FimForce(_init);
}

void FimForce_fini_function(void * message_memory)
{
  auto typed_message = static_cast<genie_msgs::msg::FimForce *>(message_memory);
  typed_message->~FimForce();
}

size_t size_function__FimForce__fim_force(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<uint8_t> *>(untyped_member);
  return member->size();
}

const void * get_const_function__FimForce__fim_force(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<uint8_t> *>(untyped_member);
  return &member[index];
}

void * get_function__FimForce__fim_force(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<uint8_t> *>(untyped_member);
  return &member[index];
}

void fetch_function__FimForce__fim_force(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & item = *reinterpret_cast<const uint8_t *>(
    get_const_function__FimForce__fim_force(untyped_member, index));
  auto & value = *reinterpret_cast<uint8_t *>(untyped_value);
  value = item;
}

void assign_function__FimForce__fim_force(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & item = *reinterpret_cast<uint8_t *>(
    get_function__FimForce__fim_force(untyped_member, index));
  const auto & value = *reinterpret_cast<const uint8_t *>(untyped_value);
  item = value;
}

void resize_function__FimForce__fim_force(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<uint8_t> *>(untyped_member);
  member->resize(size);
}

size_t size_function__FimForce__force_err_code(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<uint16_t> *>(untyped_member);
  return member->size();
}

const void * get_const_function__FimForce__force_err_code(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<uint16_t> *>(untyped_member);
  return &member[index];
}

void * get_function__FimForce__force_err_code(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<uint16_t> *>(untyped_member);
  return &member[index];
}

void fetch_function__FimForce__force_err_code(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & item = *reinterpret_cast<const uint16_t *>(
    get_const_function__FimForce__force_err_code(untyped_member, index));
  auto & value = *reinterpret_cast<uint16_t *>(untyped_value);
  value = item;
}

void assign_function__FimForce__force_err_code(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & item = *reinterpret_cast<uint16_t *>(
    get_function__FimForce__force_err_code(untyped_member, index));
  const auto & value = *reinterpret_cast<const uint16_t *>(untyped_value);
  item = value;
}

void resize_function__FimForce__force_err_code(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<uint16_t> *>(untyped_member);
  member->resize(size);
}

static const ::rosidl_typesupport_introspection_cpp::MessageMember FimForce_message_member_array[3] = {
  {
    "header",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<std_msgs::msg::Header>(),  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs::msg::FimForce, header),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "fim_force",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_UINT8,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs::msg::FimForce, fim_force),  // bytes offset in struct
    nullptr,  // default value
    size_function__FimForce__fim_force,  // size() function pointer
    get_const_function__FimForce__fim_force,  // get_const(index) function pointer
    get_function__FimForce__fim_force,  // get(index) function pointer
    fetch_function__FimForce__fim_force,  // fetch(index, &value) function pointer
    assign_function__FimForce__fim_force,  // assign(index, value) function pointer
    resize_function__FimForce__fim_force  // resize(index) function pointer
  },
  {
    "force_err_code",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_UINT16,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs::msg::FimForce, force_err_code),  // bytes offset in struct
    nullptr,  // default value
    size_function__FimForce__force_err_code,  // size() function pointer
    get_const_function__FimForce__force_err_code,  // get_const(index) function pointer
    get_function__FimForce__force_err_code,  // get(index) function pointer
    fetch_function__FimForce__force_err_code,  // fetch(index, &value) function pointer
    assign_function__FimForce__force_err_code,  // assign(index, value) function pointer
    resize_function__FimForce__force_err_code  // resize(index) function pointer
  }
};

static const ::rosidl_typesupport_introspection_cpp::MessageMembers FimForce_message_members = {
  "genie_msgs::msg",  // message namespace
  "FimForce",  // message name
  3,  // number of fields
  sizeof(genie_msgs::msg::FimForce),
  FimForce_message_member_array,  // message members
  FimForce_init_function,  // function to initialize message memory (memory has to be allocated)
  FimForce_fini_function  // function to terminate message instance (will not free memory)
};

static const rosidl_message_type_support_t FimForce_message_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &FimForce_message_members,
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
get_message_type_support_handle<genie_msgs::msg::FimForce>()
{
  return &::genie_msgs::msg::rosidl_typesupport_introspection_cpp::FimForce_message_type_support_handle;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, genie_msgs, msg, FimForce)() {
  return &::genie_msgs::msg::rosidl_typesupport_introspection_cpp::FimForce_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif
