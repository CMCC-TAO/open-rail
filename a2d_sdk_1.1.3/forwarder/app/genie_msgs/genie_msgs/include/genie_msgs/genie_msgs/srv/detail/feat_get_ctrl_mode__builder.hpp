// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:srv/FeatGetCtrlMode.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__FEAT_GET_CTRL_MODE__BUILDER_HPP_
#define GENIE_MSGS__SRV__DETAIL__FEAT_GET_CTRL_MODE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/srv/detail/feat_get_ctrl_mode__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_FeatGetCtrlMode_Request_header
{
public:
  Init_FeatGetCtrlMode_Request_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::genie_msgs::srv::FeatGetCtrlMode_Request header(::genie_msgs::srv::FeatGetCtrlMode_Request::_header_type arg)
  {
    msg_.header = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::FeatGetCtrlMode_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::FeatGetCtrlMode_Request>()
{
  return genie_msgs::srv::builder::Init_FeatGetCtrlMode_Request_header();
}

}  // namespace genie_msgs


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_FeatGetCtrlMode_Response_exec_result
{
public:
  explicit Init_FeatGetCtrlMode_Response_exec_result(::genie_msgs::srv::FeatGetCtrlMode_Response & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::FeatGetCtrlMode_Response exec_result(::genie_msgs::srv::FeatGetCtrlMode_Response::_exec_result_type arg)
  {
    msg_.exec_result = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::FeatGetCtrlMode_Response msg_;
};

class Init_FeatGetCtrlMode_Response_ctrl_mode
{
public:
  explicit Init_FeatGetCtrlMode_Response_ctrl_mode(::genie_msgs::srv::FeatGetCtrlMode_Response & msg)
  : msg_(msg)
  {}
  Init_FeatGetCtrlMode_Response_exec_result ctrl_mode(::genie_msgs::srv::FeatGetCtrlMode_Response::_ctrl_mode_type arg)
  {
    msg_.ctrl_mode = std::move(arg);
    return Init_FeatGetCtrlMode_Response_exec_result(msg_);
  }

private:
  ::genie_msgs::srv::FeatGetCtrlMode_Response msg_;
};

class Init_FeatGetCtrlMode_Response_remote_mode
{
public:
  explicit Init_FeatGetCtrlMode_Response_remote_mode(::genie_msgs::srv::FeatGetCtrlMode_Response & msg)
  : msg_(msg)
  {}
  Init_FeatGetCtrlMode_Response_ctrl_mode remote_mode(::genie_msgs::srv::FeatGetCtrlMode_Response::_remote_mode_type arg)
  {
    msg_.remote_mode = std::move(arg);
    return Init_FeatGetCtrlMode_Response_ctrl_mode(msg_);
  }

private:
  ::genie_msgs::srv::FeatGetCtrlMode_Response msg_;
};

class Init_FeatGetCtrlMode_Response_online
{
public:
  explicit Init_FeatGetCtrlMode_Response_online(::genie_msgs::srv::FeatGetCtrlMode_Response & msg)
  : msg_(msg)
  {}
  Init_FeatGetCtrlMode_Response_remote_mode online(::genie_msgs::srv::FeatGetCtrlMode_Response::_online_type arg)
  {
    msg_.online = std::move(arg);
    return Init_FeatGetCtrlMode_Response_remote_mode(msg_);
  }

private:
  ::genie_msgs::srv::FeatGetCtrlMode_Response msg_;
};

class Init_FeatGetCtrlMode_Response_res_header
{
public:
  Init_FeatGetCtrlMode_Response_res_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_FeatGetCtrlMode_Response_online res_header(::genie_msgs::srv::FeatGetCtrlMode_Response::_res_header_type arg)
  {
    msg_.res_header = std::move(arg);
    return Init_FeatGetCtrlMode_Response_online(msg_);
  }

private:
  ::genie_msgs::srv::FeatGetCtrlMode_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::FeatGetCtrlMode_Response>()
{
  return genie_msgs::srv::builder::Init_FeatGetCtrlMode_Response_res_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__SRV__DETAIL__FEAT_GET_CTRL_MODE__BUILDER_HPP_
