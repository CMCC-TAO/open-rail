// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:srv/AGVSetColor.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__AGV_SET_COLOR__BUILDER_HPP_
#define GENIE_MSGS__SRV__DETAIL__AGV_SET_COLOR__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/srv/detail/agv_set_color__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_AGVSetColor_Request_freqency
{
public:
  explicit Init_AGVSetColor_Request_freqency(::genie_msgs::srv::AGVSetColor_Request & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::AGVSetColor_Request freqency(::genie_msgs::srv::AGVSetColor_Request::_freqency_type arg)
  {
    msg_.freqency = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::AGVSetColor_Request msg_;
};

class Init_AGVSetColor_Request_ctrl_mode
{
public:
  explicit Init_AGVSetColor_Request_ctrl_mode(::genie_msgs::srv::AGVSetColor_Request & msg)
  : msg_(msg)
  {}
  Init_AGVSetColor_Request_freqency ctrl_mode(::genie_msgs::srv::AGVSetColor_Request::_ctrl_mode_type arg)
  {
    msg_.ctrl_mode = std::move(arg);
    return Init_AGVSetColor_Request_freqency(msg_);
  }

private:
  ::genie_msgs::srv::AGVSetColor_Request msg_;
};

class Init_AGVSetColor_Request_color_rgba
{
public:
  explicit Init_AGVSetColor_Request_color_rgba(::genie_msgs::srv::AGVSetColor_Request & msg)
  : msg_(msg)
  {}
  Init_AGVSetColor_Request_ctrl_mode color_rgba(::genie_msgs::srv::AGVSetColor_Request::_color_rgba_type arg)
  {
    msg_.color_rgba = std::move(arg);
    return Init_AGVSetColor_Request_ctrl_mode(msg_);
  }

private:
  ::genie_msgs::srv::AGVSetColor_Request msg_;
};

class Init_AGVSetColor_Request_header
{
public:
  Init_AGVSetColor_Request_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_AGVSetColor_Request_color_rgba header(::genie_msgs::srv::AGVSetColor_Request::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_AGVSetColor_Request_color_rgba(msg_);
  }

private:
  ::genie_msgs::srv::AGVSetColor_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::AGVSetColor_Request>()
{
  return genie_msgs::srv::builder::Init_AGVSetColor_Request_header();
}

}  // namespace genie_msgs


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_AGVSetColor_Response_exec_result
{
public:
  explicit Init_AGVSetColor_Response_exec_result(::genie_msgs::srv::AGVSetColor_Response & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::AGVSetColor_Response exec_result(::genie_msgs::srv::AGVSetColor_Response::_exec_result_type arg)
  {
    msg_.exec_result = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::AGVSetColor_Response msg_;
};

class Init_AGVSetColor_Response_res_header
{
public:
  Init_AGVSetColor_Response_res_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_AGVSetColor_Response_exec_result res_header(::genie_msgs::srv::AGVSetColor_Response::_res_header_type arg)
  {
    msg_.res_header = std::move(arg);
    return Init_AGVSetColor_Response_exec_result(msg_);
  }

private:
  ::genie_msgs::srv::AGVSetColor_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::AGVSetColor_Response>()
{
  return genie_msgs::srv::builder::Init_AGVSetColor_Response_res_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__SRV__DETAIL__AGV_SET_COLOR__BUILDER_HPP_
