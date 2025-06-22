// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:srv/ForceInit.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__FORCE_INIT__BUILDER_HPP_
#define GENIE_MSGS__SRV__DETAIL__FORCE_INIT__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/srv/detail/force_init__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_ForceInit_Request_block
{
public:
  explicit Init_ForceInit_Request_block(::genie_msgs::srv::ForceInit_Request & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::ForceInit_Request block(::genie_msgs::srv::ForceInit_Request::_block_type arg)
  {
    msg_.block = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::ForceInit_Request msg_;
};

class Init_ForceInit_Request_force_id
{
public:
  explicit Init_ForceInit_Request_force_id(::genie_msgs::srv::ForceInit_Request & msg)
  : msg_(msg)
  {}
  Init_ForceInit_Request_block force_id(::genie_msgs::srv::ForceInit_Request::_force_id_type arg)
  {
    msg_.force_id = std::move(arg);
    return Init_ForceInit_Request_block(msg_);
  }

private:
  ::genie_msgs::srv::ForceInit_Request msg_;
};

class Init_ForceInit_Request_header
{
public:
  Init_ForceInit_Request_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ForceInit_Request_force_id header(::genie_msgs::srv::ForceInit_Request::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_ForceInit_Request_force_id(msg_);
  }

private:
  ::genie_msgs::srv::ForceInit_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::ForceInit_Request>()
{
  return genie_msgs::srv::builder::Init_ForceInit_Request_header();
}

}  // namespace genie_msgs


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_ForceInit_Response_exec_result
{
public:
  explicit Init_ForceInit_Response_exec_result(::genie_msgs::srv::ForceInit_Response & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::ForceInit_Response exec_result(::genie_msgs::srv::ForceInit_Response::_exec_result_type arg)
  {
    msg_.exec_result = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::ForceInit_Response msg_;
};

class Init_ForceInit_Response_res_header
{
public:
  Init_ForceInit_Response_res_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ForceInit_Response_exec_result res_header(::genie_msgs::srv::ForceInit_Response::_res_header_type arg)
  {
    msg_.res_header = std::move(arg);
    return Init_ForceInit_Response_exec_result(msg_);
  }

private:
  ::genie_msgs::srv::ForceInit_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::ForceInit_Response>()
{
  return genie_msgs::srv::builder::Init_ForceInit_Response_res_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__SRV__DETAIL__FORCE_INIT__BUILDER_HPP_
