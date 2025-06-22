// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/FimForce.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FIM_FORCE__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__FIM_FORCE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/fim_force__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_FimForce_force_err_code
{
public:
  explicit Init_FimForce_force_err_code(::genie_msgs::msg::FimForce & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::FimForce force_err_code(::genie_msgs::msg::FimForce::_force_err_code_type arg)
  {
    msg_.force_err_code = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::FimForce msg_;
};

class Init_FimForce_fim_force
{
public:
  explicit Init_FimForce_fim_force(::genie_msgs::msg::FimForce & msg)
  : msg_(msg)
  {}
  Init_FimForce_force_err_code fim_force(::genie_msgs::msg::FimForce::_fim_force_type arg)
  {
    msg_.fim_force = std::move(arg);
    return Init_FimForce_force_err_code(msg_);
  }

private:
  ::genie_msgs::msg::FimForce msg_;
};

class Init_FimForce_header
{
public:
  Init_FimForce_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_FimForce_fim_force header(::genie_msgs::msg::FimForce::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_FimForce_fim_force(msg_);
  }

private:
  ::genie_msgs::msg::FimForce msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::FimForce>()
{
  return genie_msgs::msg::builder::Init_FimForce_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__FIM_FORCE__BUILDER_HPP_
