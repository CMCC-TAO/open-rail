// generated from rosidl_typesupport_introspection_cpp/resource/idl__type_support.cpp.em
// with input from genie_msgs:msg/FimEE.idl
// generated code does not contain a copyright notice

#include "array"
#include "cstddef"
#include "string"
#include "vector"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_interface/macros.h"
#include "genie_msgs/msg/detail/fim_ee__struct.hpp"
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

void FimEE_init_function(
  void * message_memory, rosidl_runtime_cpp::MessageInitialization _init)
{
  new (message_memory) genie_msgs::msg::FimEE(_init);
}

void FimEE_fini_function(void * message_memory)
{
  auto typed_message = static_cast<genie_msgs::msg::FimEE *>(message_memory);
  typed_message->~FimEE();
}

size_t size_function__FimEE__fim_ee(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<uint8_t> *>(untyped_member);
  return member->size();
}

const void * get_const_function__FimEE__fim_ee(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<uint8_t> *>(untyped_member);
  return &member[index];
}

void * get_function__FimEE__fim_ee(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<uint8_t> *>(untyped_member);
  return &member[index];
}

void fetch_function__FimEE__fim_ee(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & item = *reinterpret_cast<const uint8_t *>(
    get_const_function__FimEE__fim_ee(untyped_member, index));
  auto & value = *reinterpret_cast<uint8_t *>(untyped_value);
  value = item;
}

void assign_function__FimEE__fim_ee(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & item = *reinterpret_cast<uint8_t *>(
    get_function__FimEE__fim_ee(untyped_member, index));
  const auto & value = *reinterpret_cast<const uint8_t *>(untyped_value);
  item = value;
}

void resize_function__FimEE__fim_ee(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<uint8_t> *>(untyped_member);
  member->resize(size);
}

size_t size_function__FimEE__ee_err_code(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<uint16_t> *>(untyped_member);
  return member->size();
}

const void * get_const_function__FimEE__ee_err_code(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<uint16_t> *>(untyped_member);
  return &member[index];
}

void * get_function__FimEE__ee_err_code(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<uint16_t> *>(untyped_member);
  return &member[index];
}

void fetch_function__FimEE__ee_err_code(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & item = *reinterpret_cast<const uint16_t *>(
    get_const_function__FimEE__ee_err_code(untyped_member, index));
  auto & value = *reinterpret_cast<uint16_t *>(untyped_value);
  value = item;
}

void assign_function__FimEE__ee_err_code(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & item = *reinterpret_cast<uint16_t *>(
    get_function__FimEE__ee_err_code(untyped_member, index));
  const auto & value = *reinterpret_cast<const uint16_t *>(untyped_value);
  item = value;
}

void resize_function__FimEE__ee_err_code(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<uint16_t> *>(untyped_member);
  member->resize(size);
}

static const ::rosidl_typesupport_introspection_cpp::MessageMember FimEE_message_member_array[3] = {
  {
    "header",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<std_msgs::msg::Header>(),  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs::msg::FimEE, header),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "fim_ee",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_UINT8,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs::msg::FimEE, fim_ee),  // bytes offset in struct
    nullptr,  // default value
    size_function__FimEE__fim_ee,  // size() function pointer
    get_const_function__FimEE__fim_ee,  // get_const(index) function pointer
    get_function__FimEE__fim_ee,  // get(index) function pointer
    fetch_function__FimEE__fim_ee,  // fetch(index, &value) function pointer
    assign_function__FimEE__fim_ee,  // assign(index, value) function pointer
    resize_function__FimEE__fim_ee  // resize(index) function pointer
  },
  {
    "ee_err_code",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_UINT16,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs::msg::FimEE, ee_err_code),  // bytes offset in struct
    nullptr,  // default value
    size_function__FimEE__ee_err_code,  // size() function pointer
    get_const_function__FimEE__ee_err_code,  // get_const(index) function pointer
    get_function__FimEE__ee_err_code,  // get(index) function pointer
    fetch_function__FimEE__ee_err_code,  // fetch(index, &value) function pointer
    assign_function__FimEE__ee_err_code,  // assign(index, value) function pointer
    resize_function__FimEE__ee_err_code  // resize(index) function pointer
  }
};

static const ::rosidl_typesupport_introspection_cpp::MessageMembers FimEE_message_members = {
  "genie_msgs::msg",  // message namespace
  "FimEE",  // message name
  3,  // number of fields
  sizeof(genie_msgs::msg::FimEE),
  FimEE_message_member_array,  // message members
  FimEE_init_function,  // function to initialize message memory (memory has to be allocated)
  FimEE_fini_function  // function to terminate message instance (will not free memory)
};

static const rosidl_message_type_support_t FimEE_message_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &FimEE_message_members,
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
get_message_type_support_handle<genie_msgs::msg::FimEE>()
{
  return &::genie_msgs::msg::rosidl_typesupport_introspection_cpp::FimEE_message_type_support_handle;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, genie_msgs, msg, FimEE)() {
  return &::genie_msgs::msg::rosidl_typesupport_introspection_cpp::FimEE_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif
