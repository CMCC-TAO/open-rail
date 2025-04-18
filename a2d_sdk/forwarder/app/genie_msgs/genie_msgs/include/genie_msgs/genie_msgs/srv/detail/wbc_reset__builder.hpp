// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:srv/WbcReset.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__WBC_RESET__BUILDER_HPP_
#define GENIE_MSGS__SRV__DETAIL__WBC_RESET__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/srv/detail/wbc_reset__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_WbcReset_Request_header
{
public:
  Init_WbcReset_Request_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::genie_msgs::srv::WbcReset_Request header(::genie_msgs::srv::WbcReset_Request::_header_type arg)
  {
    msg_.header = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::WbcReset_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::WbcReset_Request>()
{
  return genie_msgs::srv::builder::Init_WbcReset_Request_header();
}

}  // namespace genie_msgs


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_WbcReset_Response_res_header
{
public:
  Init_WbcReset_Response_res_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::genie_msgs::srv::WbcReset_Response res_header(::genie_msgs::srv::WbcReset_Response::_res_header_type arg)
  {
    msg_.res_header = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::WbcReset_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::WbcReset_Response>()
{
  return genie_msgs::srv::builder::Init_WbcReset_Response_res_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__SRV__DETAIL__WBC_RESET__BUILDER_HPP_
