// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:srv/WbcStop.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__WBC_STOP__BUILDER_HPP_
#define GENIE_MSGS__SRV__DETAIL__WBC_STOP__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/srv/detail/wbc_stop__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_WbcStop_Request_header
{
public:
  Init_WbcStop_Request_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::genie_msgs::srv::WbcStop_Request header(::genie_msgs::srv::WbcStop_Request::_header_type arg)
  {
    msg_.header = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::WbcStop_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::WbcStop_Request>()
{
  return genie_msgs::srv::builder::Init_WbcStop_Request_header();
}

}  // namespace genie_msgs


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_WbcStop_Response_stop_flag
{
public:
  explicit Init_WbcStop_Response_stop_flag(::genie_msgs::srv::WbcStop_Response & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::WbcStop_Response stop_flag(::genie_msgs::srv::WbcStop_Response::_stop_flag_type arg)
  {
    msg_.stop_flag = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::WbcStop_Response msg_;
};

class Init_WbcStop_Response_res_header
{
public:
  Init_WbcStop_Response_res_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_WbcStop_Response_stop_flag res_header(::genie_msgs::srv::WbcStop_Response::_res_header_type arg)
  {
    msg_.res_header = std::move(arg);
    return Init_WbcStop_Response_stop_flag(msg_);
  }

private:
  ::genie_msgs::srv::WbcStop_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::WbcStop_Response>()
{
  return genie_msgs::srv::builder::Init_WbcStop_Response_res_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__SRV__DETAIL__WBC_STOP__BUILDER_HPP_
