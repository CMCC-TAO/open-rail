// generated from rosidl_typesupport_introspection_cpp/resource/idl__type_support.cpp.em
// with input from genie_msgs:srv/ForceInfo.idl
// generated code does not contain a copyright notice

#include "array"
#include "cstddef"
#include "string"
#include "vector"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_interface/macros.h"
#include "genie_msgs/srv/detail/force_info__struct.hpp"
#include "rosidl_typesupport_introspection_cpp/field_types.hpp"
#include "rosidl_typesupport_introspection_cpp/identifier.hpp"
#include "rosidl_typesupport_introspection_cpp/message_introspection.hpp"
#include "rosidl_typesupport_introspection_cpp/message_type_support_decl.hpp"
#include "rosidl_typesupport_introspection_cpp/visibility_control.h"

namespace genie_msgs
{

namespace srv
{

namespace rosidl_typesupport_introspection_cpp
{

void ForceInfo_Request_init_function(
  void * message_memory, rosidl_runtime_cpp::MessageInitialization _init)
{
  new (message_memory) genie_msgs::srv::ForceInfo_Request(_init);
}

void ForceInfo_Request_fini_function(void * message_memory)
{
  auto typed_message = static_cast<genie_msgs::srv::ForceInfo_Request *>(message_memory);
  typed_message->~ForceInfo_Request();
}

static const ::rosidl_typesupport_introspection_cpp::MessageMember ForceInfo_Request_message_member_array[2] = {
  {
    "header",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<std_msgs::msg::Header>(),  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs::srv::ForceInfo_Request, header),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "force_id",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_UINT32,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs::srv::ForceInfo_Request, force_id),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  }
};

static const ::rosidl_typesupport_introspection_cpp::MessageMembers ForceInfo_Request_message_members = {
  "genie_msgs::srv",  // message namespace
  "ForceInfo_Request",  // message name
  2,  // number of fields
  sizeof(genie_msgs::srv::ForceInfo_Request),
  ForceInfo_Request_message_member_array,  // message members
  ForceInfo_Request_init_function,  // function to initialize message memory (memory has to be allocated)
  ForceInfo_Request_fini_function  // function to terminate message instance (will not free memory)
};

static const rosidl_message_type_support_t ForceInfo_Request_message_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &ForceInfo_Request_message_members,
  get_message_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_introspection_cpp

}  // namespace srv

}  // namespace genie_msgs


namespace rosidl_typesupport_introspection_cpp
{

template<>
ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<genie_msgs::srv::ForceInfo_Request>()
{
  return &::genie_msgs::srv::rosidl_typesupport_introspection_cpp::ForceInfo_Request_message_type_support_handle;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, genie_msgs, srv, ForceInfo_Request)() {
  return &::genie_msgs::srv::rosidl_typesupport_introspection_cpp::ForceInfo_Request_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "array"
// already included above
// #include "cstddef"
// already included above
// #include "string"
// already included above
// #include "vector"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support.hpp"
// already included above
// #include "rosidl_typesupport_interface/macros.h"
// already included above
// #include "genie_msgs/srv/detail/force_info__struct.hpp"
// already included above
// #include "rosidl_typesupport_introspection_cpp/field_types.hpp"
// already included above
// #include "rosidl_typesupport_introspection_cpp/identifier.hpp"
// already included above
// #include "rosidl_typesupport_introspection_cpp/message_introspection.hpp"
// already included above
// #include "rosidl_typesupport_introspection_cpp/message_type_support_decl.hpp"
// already included above
// #include "rosidl_typesupport_introspection_cpp/visibility_control.h"

namespace genie_msgs
{

namespace srv
{

namespace rosidl_typesupport_introspection_cpp
{

void ForceInfo_Response_init_function(
  void * message_memory, rosidl_runtime_cpp::MessageInitialization _init)
{
  new (message_memory) genie_msgs::srv::ForceInfo_Response(_init);
}

void ForceInfo_Response_fini_function(void * message_memory)
{
  auto typed_message = static_cast<genie_msgs::srv::ForceInfo_Response *>(message_memory);
  typed_message->~ForceInfo_Response();
}

size_t size_function__ForceInfo_Response__work_zero_force_data(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<double> *>(untyped_member);
  return member->size();
}

const void * get_const_function__ForceInfo_Response__work_zero_force_data(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<double> *>(untyped_member);
  return &member[index];
}

void * get_function__ForceInfo_Response__work_zero_force_data(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<double> *>(untyped_member);
  return &member[index];
}

void fetch_function__ForceInfo_Response__work_zero_force_data(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & item = *reinterpret_cast<const double *>(
    get_const_function__ForceInfo_Response__work_zero_force_data(untyped_member, index));
  auto & value = *reinterpret_cast<double *>(untyped_value);
  value = item;
}

void assign_function__ForceInfo_Response__work_zero_force_data(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & item = *reinterpret_cast<double *>(
    get_function__ForceInfo_Response__work_zero_force_data(untyped_member, index));
  const auto & value = *reinterpret_cast<const double *>(untyped_value);
  item = value;
}

void resize_function__ForceInfo_Response__work_zero_force_data(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<double> *>(untyped_member);
  member->resize(size);
}

size_t size_function__ForceInfo_Response__tool_zero_force_data(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<double> *>(untyped_member);
  return member->size();
}

const void * get_const_function__ForceInfo_Response__tool_zero_force_data(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<double> *>(untyped_member);
  return &member[index];
}

void * get_function__ForceInfo_Response__tool_zero_force_data(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<double> *>(untyped_member);
  return &member[index];
}

void fetch_function__ForceInfo_Response__tool_zero_force_data(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & item = *reinterpret_cast<const double *>(
    get_const_function__ForceInfo_Response__tool_zero_force_data(untyped_member, index));
  auto & value = *reinterpret_cast<double *>(untyped_value);
  value = item;
}

void assign_function__ForceInfo_Response__tool_zero_force_data(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & item = *reinterpret_cast<double *>(
    get_function__ForceInfo_Response__tool_zero_force_data(untyped_member, index));
  const auto & value = *reinterpret_cast<const double *>(untyped_value);
  item = value;
}

void resize_function__ForceInfo_Response__tool_zero_force_data(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<double> *>(untyped_member);
  member->resize(size);
}

size_t size_function__ForceInfo_Response__zero_force_data(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<double> *>(untyped_member);
  return member->size();
}

const void * get_const_function__ForceInfo_Response__zero_force_data(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<double> *>(untyped_member);
  return &member[index];
}

void * get_function__ForceInfo_Response__zero_force_data(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<double> *>(untyped_member);
  return &member[index];
}

void fetch_function__ForceInfo_Response__zero_force_data(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & item = *reinterpret_cast<const double *>(
    get_const_function__ForceInfo_Response__zero_force_data(untyped_member, index));
  auto & value = *reinterpret_cast<double *>(untyped_value);
  value = item;
}

void assign_function__ForceInfo_Response__zero_force_data(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & item = *reinterpret_cast<double *>(
    get_function__ForceInfo_Response__zero_force_data(untyped_member, index));
  const auto & value = *reinterpret_cast<const double *>(untyped_value);
  item = value;
}

void resize_function__ForceInfo_Response__zero_force_data(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<double> *>(untyped_member);
  member->resize(size);
}

static const ::rosidl_typesupport_introspection_cpp::MessageMember ForceInfo_Response_message_member_array[5] = {
  {
    "res_header",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<std_msgs::msg::Header>(),  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs::srv::ForceInfo_Response, res_header),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "exec_result",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_UINT8,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs::srv::ForceInfo_Response, exec_result),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "work_zero_force_data",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs::srv::ForceInfo_Response, work_zero_force_data),  // bytes offset in struct
    nullptr,  // default value
    size_function__ForceInfo_Response__work_zero_force_data,  // size() function pointer
    get_const_function__ForceInfo_Response__work_zero_force_data,  // get_const(index) function pointer
    get_function__ForceInfo_Response__work_zero_force_data,  // get(index) function pointer
    fetch_function__ForceInfo_Response__work_zero_force_data,  // fetch(index, &value) function pointer
    assign_function__ForceInfo_Response__work_zero_force_data,  // assign(index, value) function pointer
    resize_function__ForceInfo_Response__work_zero_force_data  // resize(index) function pointer
  },
  {
    "tool_zero_force_data",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs::srv::ForceInfo_Response, tool_zero_force_data),  // bytes offset in struct
    nullptr,  // default value
    size_function__ForceInfo_Response__tool_zero_force_data,  // size() function pointer
    get_const_function__ForceInfo_Response__tool_zero_force_data,  // get_const(index) function pointer
    get_function__ForceInfo_Response__tool_zero_force_data,  // get(index) function pointer
    fetch_function__ForceInfo_Response__tool_zero_force_data,  // fetch(index, &value) function pointer
    assign_function__ForceInfo_Response__tool_zero_force_data,  // assign(index, value) function pointer
    resize_function__ForceInfo_Response__tool_zero_force_data  // resize(index) function pointer
  },
  {
    "zero_force_data",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_DOUBLE,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(genie_msgs::srv::ForceInfo_Response, zero_force_data),  // bytes offset in struct
    nullptr,  // default value
    size_function__ForceInfo_Response__zero_force_data,  // size() function pointer
    get_const_function__ForceInfo_Response__zero_force_data,  // get_const(index) function pointer
    get_function__ForceInfo_Response__zero_force_data,  // get(index) function pointer
    fetch_function__ForceInfo_Response__zero_force_data,  // fetch(index, &value) function pointer
    assign_function__ForceInfo_Response__zero_force_data,  // assign(index, value) function pointer
    resize_function__ForceInfo_Response__zero_force_data  // resize(index) function pointer
  }
};

static const ::rosidl_typesupport_introspection_cpp::MessageMembers ForceInfo_Response_message_members = {
  "genie_msgs::srv",  // message namespace
  "ForceInfo_Response",  // message name
  5,  // number of fields
  sizeof(genie_msgs::srv::ForceInfo_Response),
  ForceInfo_Response_message_member_array,  // message members
  ForceInfo_Response_init_function,  // function to initialize message memory (memory has to be allocated)
  ForceInfo_Response_fini_function  // function to terminate message instance (will not free memory)
};

static const rosidl_message_type_support_t ForceInfo_Response_message_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &ForceInfo_Response_message_members,
  get_message_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_introspection_cpp

}  // namespace srv

}  // namespace genie_msgs


namespace rosidl_typesupport_introspection_cpp
{

template<>
ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<genie_msgs::srv::ForceInfo_Response>()
{
  return &::genie_msgs::srv::rosidl_typesupport_introspection_cpp::ForceInfo_Response_message_type_support_handle;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, genie_msgs, srv, ForceInfo_Response)() {
  return &::genie_msgs::srv::rosidl_typesupport_introspection_cpp::ForceInfo_Response_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif

#include "rosidl_runtime_c/service_type_support_struct.h"
// already included above
// #include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_cpp/service_type_support.hpp"
// already included above
// #include "rosidl_typesupport_interface/macros.h"
// already included above
// #include "rosidl_typesupport_introspection_cpp/visibility_control.h"
// already included above
// #include "genie_msgs/srv/detail/force_info__struct.hpp"
// already included above
// #include "rosidl_typesupport_introspection_cpp/identifier.hpp"
// already included above
// #include "rosidl_typesupport_introspection_cpp/message_type_support_decl.hpp"
#include "rosidl_typesupport_introspection_cpp/service_introspection.hpp"
#include "rosidl_typesupport_introspection_cpp/service_type_support_decl.hpp"

namespace genie_msgs
{

namespace srv
{

namespace rosidl_typesupport_introspection_cpp
{

// this is intentionally not const to allow initialization later to prevent an initialization race
static ::rosidl_typesupport_introspection_cpp::ServiceMembers ForceInfo_service_members = {
  "genie_msgs::srv",  // service namespace
  "ForceInfo",  // service name
  // these two fields are initialized below on the first access
  // see get_service_type_support_handle<genie_msgs::srv::ForceInfo>()
  nullptr,  // request message
  nullptr  // response message
};

static const rosidl_service_type_support_t ForceInfo_service_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &ForceInfo_service_members,
  get_service_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_introspection_cpp

}  // namespace srv

}  // namespace genie_msgs


namespace rosidl_typesupport_introspection_cpp
{

template<>
ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_service_type_support_t *
get_service_type_support_handle<genie_msgs::srv::ForceInfo>()
{
  // get a handle to the value to be returned
  auto service_type_support =
    &::genie_msgs::srv::rosidl_typesupport_introspection_cpp::ForceInfo_service_type_support_handle;
  // get a non-const and properly typed version of the data void *
  auto service_members = const_cast<::rosidl_typesupport_introspection_cpp::ServiceMembers *>(
    static_cast<const ::rosidl_typesupport_introspection_cpp::ServiceMembers *>(
      service_type_support->data));
  // make sure that both the request_members_ and the response_members_ are initialized
  // if they are not, initialize them
  if (
    service_members->request_members_ == nullptr ||
    service_members->response_members_ == nullptr)
  {
    // initialize the request_members_ with the static function from the external library
    service_members->request_members_ = static_cast<
      const ::rosidl_typesupport_introspection_cpp::MessageMembers *
      >(
      ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<
        ::genie_msgs::srv::ForceInfo_Request
      >()->data
      );
    // initialize the response_members_ with the static function from the external library
    service_members->response_members_ = static_cast<
      const ::rosidl_typesupport_introspection_cpp::MessageMembers *
      >(
      ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<
        ::genie_msgs::srv::ForceInfo_Response
      >()->data
      );
  }
  // finally return the properly initialized service_type_support handle
  return service_type_support;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_service_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, genie_msgs, srv, ForceInfo)() {
  return ::rosidl_typesupport_introspection_cpp::get_service_type_support_handle<genie_msgs::srv::ForceInfo>();
}

#ifdef __cplusplus
}
#endif
