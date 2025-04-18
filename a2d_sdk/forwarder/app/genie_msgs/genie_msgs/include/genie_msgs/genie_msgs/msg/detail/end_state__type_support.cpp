// generated from rosidl_typesupport_introspection_cpp/resource/idl__type_support.cpp.em
// with input from genie_msgs:msg/EndState.idl
// generated code does not contain a copyright notice

#include "array"
#include "cstddef"
#include "string"
#include "vector"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_interface/macros.h"
#include "genie_msgs/msg/detail/end_state__struct.hpp"
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

void EndState_init_function(
  void * message_memory, rosidl_runtime_cpp::MessageInitialization _init)
{
  new (message_memory) genie_msgs::msg::EndState(_init);
}

void EndState_fini_function(void * message_memory)
{
  auto typed_message = static_cast<genie_msgs::msg::EndState *>(message_memory);
  typed_message->~EndState();
}

size_t size_function__EndState__end_state(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<genie_msgs::msg::MotorState> *>(untyped_member);
  return member->size();
}

const void * get_const_function__EndState__end_state(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<genie_msgs::msg::MotorState> *>(untyped_member);
  return &member[index];
}

void * get_function__EndState__end_state(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<genie_msgs::msg::MotorState> *>(untyped_member);
  return &member[index];
}

void fetch_function__EndState__end_state(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & item = *reinterpret_cast<const genie_msgs::msg::MotorState *>(
    get_const_function__EndState__end_state(untyped_member, index));
  auto & value = *reinterpret_cast<genie_msgs::msg::MotorState *>(untyped_value);
  value = item;
}

void assign_function__EndState__end_state(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & item = *reinterpret_cast<genie_msgs::msg::MotorState *>(
    get_function__EndState__end_state(untyped_member, index));
  const auto & value = *reinterpret_cast<const genie_msgs::msg::MotorState *>(untyped_value);
  item = value;
}

void resize_function__EndState__end_state(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<genie_msgs::msg::MotorState> *>(untyped_member);
  member->resize(size);
}

static const ::rosidl_typesupport_introspection_cpp::MessageMember EndState_message_member_array[3] = {
  {
    "header",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<std_msgs::msg::Header>(),  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs::msg::EndState, header),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "controlled",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_BOOLEAN,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs::msg::EndState, controlled),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "end_state",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<genie_msgs::msg::MotorState>(),  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs::msg::EndState, end_state),  // bytes offset in struct
    nullptr,  // default value
    size_function__EndState__end_state,  // size() function pointer
    get_const_function__EndState__end_state,  // get_const(index) function pointer
    get_function__EndState__end_state,  // get(index) function pointer
    fetch_function__EndState__end_state,  // fetch(index, &value) function pointer
    assign_function__EndState__end_state,  // assign(index, value) function pointer
    resize_function__EndState__end_state  // resize(index) function pointer
  }
};

static const ::rosidl_typesupport_introspection_cpp::MessageMembers EndState_message_members = {
  "genie_msgs::msg",  // message namespace
  "EndState",  // message name
  3,  // number of fields
  sizeof(genie_msgs::msg::EndState),
  EndState_message_member_array,  // message members
  EndState_init_function,  // function to initialize message memory (memory has to be allocated)
  EndState_fini_function  // function to terminate message instance (will not free memory)
};

static const rosidl_message_type_support_t EndState_message_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &EndState_message_members,
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
get_message_type_support_handle<genie_msgs::msg::EndState>()
{
  return &::genie_msgs::msg::rosidl_typesupport_introspection_cpp::EndState_message_type_support_handle;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, genie_msgs, msg, EndState)() {
  return &::genie_msgs::msg::rosidl_typesupport_introspection_cpp::EndState_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif
