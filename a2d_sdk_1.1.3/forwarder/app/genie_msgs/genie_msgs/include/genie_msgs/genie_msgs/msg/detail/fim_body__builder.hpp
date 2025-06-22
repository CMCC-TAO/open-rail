// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/FimBody.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FIM_BODY__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__FIM_BODY__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/fim_body__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_FimBody_lift_err_code
{
public:
  explicit Init_FimBody_lift_err_code(::genie_msgs::msg::FimBody & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::FimBody lift_err_code(::genie_msgs::msg::FimBody::_lift_err_code_type arg)
  {
    msg_.lift_err_code = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::FimBody msg_;
};

class Init_FimBody_fim_lift
{
public:
  explicit Init_FimBody_fim_lift(::genie_msgs::msg::FimBody & msg)
  : msg_(msg)
  {}
  Init_FimBody_lift_err_code fim_lift(::genie_msgs::msg::FimBody::_fim_lift_type arg)
  {
    msg_.fim_lift = std::move(arg);
    return Init_FimBody_lift_err_code(msg_);
  }

private:
  ::genie_msgs::msg::FimBody msg_;
};

class Init_FimBody_waist_err_code
{
public:
  explicit Init_FimBody_waist_err_code(::genie_msgs::msg::FimBody & msg)
  : msg_(msg)
  {}
  Init_FimBody_fim_lift waist_err_code(::genie_msgs::msg::FimBody::_waist_err_code_type arg)
  {
    msg_.waist_err_code = std::move(arg);
    return Init_FimBody_fim_lift(msg_);
  }

private:
  ::genie_msgs::msg::FimBody msg_;
};

class Init_FimBody_fim_waist
{
public:
  explicit Init_FimBody_fim_waist(::genie_msgs::msg::FimBody & msg)
  : msg_(msg)
  {}
  Init_FimBody_waist_err_code fim_waist(::genie_msgs::msg::FimBody::_fim_waist_type arg)
  {
    msg_.fim_waist = std::move(arg);
    return Init_FimBody_waist_err_code(msg_);
  }

private:
  ::genie_msgs::msg::FimBody msg_;
};

class Init_FimBody_header
{
public:
  Init_FimBody_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_FimBody_fim_waist header(::genie_msgs::msg::FimBody::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_FimBody_fim_waist(msg_);
  }

private:
  ::genie_msgs::msg::FimBody msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::FimBody>()
{
  return genie_msgs::msg::builder::Init_FimBody_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__FIM_BODY__BUILDER_HPP_
