// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:srv/WbcStart.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__WBC_START__BUILDER_HPP_
#define GENIE_MSGS__SRV__DETAIL__WBC_START__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/srv/detail/wbc_start__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_WbcStart_Request_header
{
public:
  Init_WbcStart_Request_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::genie_msgs::srv::WbcStart_Request header(::genie_msgs::srv::WbcStart_Request::_header_type arg)
  {
    msg_.header = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::WbcStart_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::WbcStart_Request>()
{
  return genie_msgs::srv::builder::Init_WbcStart_Request_header();
}

}  // namespace genie_msgs


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_WbcStart_Response_start_flag
{
public:
  explicit Init_WbcStart_Response_start_flag(::genie_msgs::srv::WbcStart_Response & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::WbcStart_Response start_flag(::genie_msgs::srv::WbcStart_Response::_start_flag_type arg)
  {
    msg_.start_flag = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::WbcStart_Response msg_;
};

class Init_WbcStart_Response_res_header
{
public:
  Init_WbcStart_Response_res_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_WbcStart_Response_start_flag res_header(::genie_msgs::srv::WbcStart_Response::_res_header_type arg)
  {
    msg_.res_header = std::move(arg);
    return Init_WbcStart_Response_start_flag(msg_);
  }

private:
  ::genie_msgs::srv::WbcStart_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::WbcStart_Response>()
{
  return genie_msgs::srv::builder::Init_WbcStart_Response_res_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__SRV__DETAIL__WBC_START__BUILDER_HPP_
