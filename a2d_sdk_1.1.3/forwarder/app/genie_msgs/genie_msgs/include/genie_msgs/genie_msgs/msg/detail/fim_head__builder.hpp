// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/FimHead.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FIM_HEAD__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__FIM_HEAD__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/fim_head__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_FimHead_neck_err_code
{
public:
  explicit Init_FimHead_neck_err_code(::genie_msgs::msg::FimHead & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::FimHead neck_err_code(::genie_msgs::msg::FimHead::_neck_err_code_type arg)
  {
    msg_.neck_err_code = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::FimHead msg_;
};

class Init_FimHead_fim_neck
{
public:
  explicit Init_FimHead_fim_neck(::genie_msgs::msg::FimHead & msg)
  : msg_(msg)
  {}
  Init_FimHead_neck_err_code fim_neck(::genie_msgs::msg::FimHead::_fim_neck_type arg)
  {
    msg_.fim_neck = std::move(arg);
    return Init_FimHead_neck_err_code(msg_);
  }

private:
  ::genie_msgs::msg::FimHead msg_;
};

class Init_FimHead_header
{
public:
  Init_FimHead_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_FimHead_fim_neck header(::genie_msgs::msg::FimHead::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_FimHead_fim_neck(msg_);
  }

private:
  ::genie_msgs::msg::FimHead msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::FimHead>()
{
  return genie_msgs::msg::builder::Init_FimHead_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__FIM_HEAD__BUILDER_HPP_
