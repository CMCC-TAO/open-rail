// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/FimEE.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FIM_EE__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__FIM_EE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/fim_ee__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_FimEE_ee_err_code
{
public:
  explicit Init_FimEE_ee_err_code(::genie_msgs::msg::FimEE & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::FimEE ee_err_code(::genie_msgs::msg::FimEE::_ee_err_code_type arg)
  {
    msg_.ee_err_code = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::FimEE msg_;
};

class Init_FimEE_fim_ee
{
public:
  explicit Init_FimEE_fim_ee(::genie_msgs::msg::FimEE & msg)
  : msg_(msg)
  {}
  Init_FimEE_ee_err_code fim_ee(::genie_msgs::msg::FimEE::_fim_ee_type arg)
  {
    msg_.fim_ee = std::move(arg);
    return Init_FimEE_ee_err_code(msg_);
  }

private:
  ::genie_msgs::msg::FimEE msg_;
};

class Init_FimEE_header
{
public:
  Init_FimEE_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_FimEE_fim_ee header(::genie_msgs::msg::FimEE::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_FimEE_fim_ee(msg_);
  }

private:
  ::genie_msgs::msg::FimEE msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::FimEE>()
{
  return genie_msgs::msg::builder::Init_FimEE_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__FIM_EE__BUILDER_HPP_
