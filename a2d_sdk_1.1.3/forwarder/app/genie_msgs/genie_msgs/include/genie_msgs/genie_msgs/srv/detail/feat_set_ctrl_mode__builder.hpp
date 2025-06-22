// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:srv/FeatSetCtrlMode.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__FEAT_SET_CTRL_MODE__BUILDER_HPP_
#define GENIE_MSGS__SRV__DETAIL__FEAT_SET_CTRL_MODE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/srv/detail/feat_set_ctrl_mode__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_FeatSetCtrlMode_Request_ctrl_mode
{
public:
  explicit Init_FeatSetCtrlMode_Request_ctrl_mode(::genie_msgs::srv::FeatSetCtrlMode_Request & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::FeatSetCtrlMode_Request ctrl_mode(::genie_msgs::srv::FeatSetCtrlMode_Request::_ctrl_mode_type arg)
  {
    msg_.ctrl_mode = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::FeatSetCtrlMode_Request msg_;
};

class Init_FeatSetCtrlMode_Request_remote_mode
{
public:
  explicit Init_FeatSetCtrlMode_Request_remote_mode(::genie_msgs::srv::FeatSetCtrlMode_Request & msg)
  : msg_(msg)
  {}
  Init_FeatSetCtrlMode_Request_ctrl_mode remote_mode(::genie_msgs::srv::FeatSetCtrlMode_Request::_remote_mode_type arg)
  {
    msg_.remote_mode = std::move(arg);
    return Init_FeatSetCtrlMode_Request_ctrl_mode(msg_);
  }

private:
  ::genie_msgs::srv::FeatSetCtrlMode_Request msg_;
};

class Init_FeatSetCtrlMode_Request_online
{
public:
  explicit Init_FeatSetCtrlMode_Request_online(::genie_msgs::srv::FeatSetCtrlMode_Request & msg)
  : msg_(msg)
  {}
  Init_FeatSetCtrlMode_Request_remote_mode online(::genie_msgs::srv::FeatSetCtrlMode_Request::_online_type arg)
  {
    msg_.online = std::move(arg);
    return Init_FeatSetCtrlMode_Request_remote_mode(msg_);
  }

private:
  ::genie_msgs::srv::FeatSetCtrlMode_Request msg_;
};

class Init_FeatSetCtrlMode_Request_header
{
public:
  Init_FeatSetCtrlMode_Request_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_FeatSetCtrlMode_Request_online header(::genie_msgs::srv::FeatSetCtrlMode_Request::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_FeatSetCtrlMode_Request_online(msg_);
  }

private:
  ::genie_msgs::srv::FeatSetCtrlMode_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::FeatSetCtrlMode_Request>()
{
  return genie_msgs::srv::builder::Init_FeatSetCtrlMode_Request_header();
}

}  // namespace genie_msgs


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_FeatSetCtrlMode_Response_exec_result
{
public:
  explicit Init_FeatSetCtrlMode_Response_exec_result(::genie_msgs::srv::FeatSetCtrlMode_Response & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::FeatSetCtrlMode_Response exec_result(::genie_msgs::srv::FeatSetCtrlMode_Response::_exec_result_type arg)
  {
    msg_.exec_result = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::FeatSetCtrlMode_Response msg_;
};

class Init_FeatSetCtrlMode_Response_res_header
{
public:
  Init_FeatSetCtrlMode_Response_res_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_FeatSetCtrlMode_Response_exec_result res_header(::genie_msgs::srv::FeatSetCtrlMode_Response::_res_header_type arg)
  {
    msg_.res_header = std::move(arg);
    return Init_FeatSetCtrlMode_Response_exec_result(msg_);
  }

private:
  ::genie_msgs::srv::FeatSetCtrlMode_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::FeatSetCtrlMode_Response>()
{
  return genie_msgs::srv::builder::Init_FeatSetCtrlMode_Response_res_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__SRV__DETAIL__FEAT_SET_CTRL_MODE__BUILDER_HPP_
