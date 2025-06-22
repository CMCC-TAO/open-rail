// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/FimRemote.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FIM_REMOTE__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__FIM_REMOTE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/fim_remote__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_FimRemote_mocap_err_code
{
public:
  explicit Init_FimRemote_mocap_err_code(::genie_msgs::msg::FimRemote & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::FimRemote mocap_err_code(::genie_msgs::msg::FimRemote::_mocap_err_code_type arg)
  {
    msg_.mocap_err_code = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::FimRemote msg_;
};

class Init_FimRemote_fim_mocap
{
public:
  explicit Init_FimRemote_fim_mocap(::genie_msgs::msg::FimRemote & msg)
  : msg_(msg)
  {}
  Init_FimRemote_mocap_err_code fim_mocap(::genie_msgs::msg::FimRemote::_fim_mocap_type arg)
  {
    msg_.fim_mocap = std::move(arg);
    return Init_FimRemote_mocap_err_code(msg_);
  }

private:
  ::genie_msgs::msg::FimRemote msg_;
};

class Init_FimRemote_vr_err_code
{
public:
  explicit Init_FimRemote_vr_err_code(::genie_msgs::msg::FimRemote & msg)
  : msg_(msg)
  {}
  Init_FimRemote_fim_mocap vr_err_code(::genie_msgs::msg::FimRemote::_vr_err_code_type arg)
  {
    msg_.vr_err_code = std::move(arg);
    return Init_FimRemote_fim_mocap(msg_);
  }

private:
  ::genie_msgs::msg::FimRemote msg_;
};

class Init_FimRemote_fim_vr
{
public:
  explicit Init_FimRemote_fim_vr(::genie_msgs::msg::FimRemote & msg)
  : msg_(msg)
  {}
  Init_FimRemote_vr_err_code fim_vr(::genie_msgs::msg::FimRemote::_fim_vr_type arg)
  {
    msg_.fim_vr = std::move(arg);
    return Init_FimRemote_vr_err_code(msg_);
  }

private:
  ::genie_msgs::msg::FimRemote msg_;
};

class Init_FimRemote_header
{
public:
  Init_FimRemote_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_FimRemote_fim_vr header(::genie_msgs::msg::FimRemote::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_FimRemote_fim_vr(msg_);
  }

private:
  ::genie_msgs::msg::FimRemote msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::FimRemote>()
{
  return genie_msgs::msg::builder::Init_FimRemote_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__FIM_REMOTE__BUILDER_HPP_
