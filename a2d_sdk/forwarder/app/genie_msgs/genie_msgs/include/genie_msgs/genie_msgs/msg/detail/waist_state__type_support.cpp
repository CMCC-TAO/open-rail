// generated from rosidl_typesupport_introspection_cpp/resource/idl__type_support.cpp.em
// with input from genie_msgs:msg/WaistState.idl
// generated code does not contain a copyright notice

#include "array"
#include "cstddef"
#include "string"
#include "vector"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_interface/macros.h"
#include "genie_msgs/msg/detail/waist_state__struct.hpp"
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

void WaistState_init_function(
  void * message_memory, rosidl_runtime_cpp::MessageInitialization _init)
{
  new (message_memory) genie_msgs::msg::WaistState(_init);
}

void WaistState_fini_function(void * message_memory)
{
  auto typed_message = static_cast<genie_msgs::msg::WaistState *>(message_memory);
  typed_message->~WaistState();
}

size_t size_function__WaistState__motor_states(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<genie_msgs::msg::MotorState> *>(untyped_member);
  return member->size();
}

const void * get_const_function__WaistState__motor_states(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<genie_msgs::msg::MotorState> *>(untyped_member);
  return &member[index];
}

void * get_function__WaistState__motor_states(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<genie_msgs::msg::MotorState> *>(untyped_member);
  return &member[index];
}

void fetch_function__WaistState__motor_states(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & item = *reinterpret_cast<const genie_msgs::msg::MotorState *>(
    get_const_function__WaistState__motor_states(untyped_member, index));
  auto & value = *reinterpret_cast<genie_msgs::msg::MotorState *>(untyped_value);
  value = item;
}

void assign_function__WaistState__motor_states(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & item = *reinterpret_cast<genie_msgs::msg::MotorState *>(
    get_function__WaistState__motor_states(untyped_member, index));
  const auto & value = *reinterpret_cast<const genie_msgs::msg::MotorState *>(untyped_value);
  item = value;
}

void resize_function__WaistState__motor_states(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<genie_msgs::msg::MotorState> *>(untyped_member);
  member->resize(size);
}

size_t size_function__WaistState__name(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<std::string> *>(untyped_member);
  return member->size();
}

const void * get_const_function__WaistState__name(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<std::string> *>(untyped_member);
  return &member[index];
}

void * get_function__WaistState__name(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<std::string> *>(untyped_member);
  return &member[index];
}

void fetch_function__WaistState__name(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & item = *reinterpret_cast<const std::string *>(
    get_const_function__WaistState__name(untyped_member, index));
  auto & value = *reinterpret_cast<std::string *>(untyped_value);
  value = item;
}

void assign_function__WaistState__name(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & item = *reinterpret_cast<std::string *>(
    get_function__WaistState__name(untyped_member, index));
  const auto & value = *reinterpret_cast<const std::string *>(untyped_value);
  item = value;
}

void resize_function__WaistState__name(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<std::string> *>(untyped_member);
  member->resize(size);
}

static const ::rosidl_typesupport_introspection_cpp::MessageMember WaistState_message_member_array[3] = {
  {
    "header",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<std_msgs::msg::Header>(),  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs::msg::WaistState, header),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "motor_states",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<genie_msgs::msg::MotorState>(),  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs::msg::WaistState, motor_states),  // bytes offset in struct
    nullptr,  // default value
    size_function__WaistState__motor_states,  // size() function pointer
    get_const_function__WaistState__motor_states,  // get_const(index) function pointer
    get_function__WaistState__motor_states,  // get(index) function pointer
    fetch_function__WaistState__motor_states,  // fetch(index, &value) function pointer
    assign_function__WaistState__motor_states,  // assign(index, value) function pointer
    resize_function__WaistState__motor_states  // resize(index) function pointer
  },
  {
    "name",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs::msg::WaistState, name),  // bytes offset in struct
    nullptr,  // default value
    size_function__WaistState__name,  // size() function pointer
    get_const_function__WaistState__name,  // get_const(index) function pointer
    get_function__WaistState__name,  // get(index) function pointer
    fetch_function__WaistState__name,  // fetch(index, &value) function pointer
    assign_function__WaistState__name,  // assign(index, value) function pointer
    resize_function__WaistState__name  // resize(index) function pointer
  }
};

static const ::rosidl_typesupport_introspection_cpp::MessageMembers WaistState_message_members = {
  "genie_msgs::msg",  // message namespace
  "WaistState",  // message name
  3,  // number of fields
  sizeof(genie_msgs::msg::WaistState),
  WaistState_message_member_array,  // message members
  WaistState_init_function,  // function to initialize message memory (memory has to be allocated)
  WaistState_fini_function  // function to terminate message instance (will not free memory)
};

static const rosidl_message_type_support_t WaistState_message_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &WaistState_message_members,
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
get_message_type_support_handle<genie_msgs::msg::WaistState>()
{
  return &::genie_msgs::msg::rosidl_typesupport_introspection_cpp::WaistState_message_type_support_handle;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, genie_msgs, msg, WaistState)() {
  return &::genie_msgs::msg::rosidl_typesupport_introspection_cpp::WaistState_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif
