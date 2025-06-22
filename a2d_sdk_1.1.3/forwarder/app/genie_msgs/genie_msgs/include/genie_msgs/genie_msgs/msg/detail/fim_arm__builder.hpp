// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/FimArm.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FIM_ARM__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__FIM_ARM__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/fim_arm__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_FimArm_arm_err_code
{
public:
  explicit Init_FimArm_arm_err_code(::genie_msgs::msg::FimArm & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::FimArm arm_err_code(::genie_msgs::msg::FimArm::_arm_err_code_type arg)
  {
    msg_.arm_err_code = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::FimArm msg_;
};

class Init_FimArm_fim_arm
{
public:
  explicit Init_FimArm_fim_arm(::genie_msgs::msg::FimArm & msg)
  : msg_(msg)
  {}
  Init_FimArm_arm_err_code fim_arm(::genie_msgs::msg::FimArm::_fim_arm_type arg)
  {
    msg_.fim_arm = std::move(arg);
    return Init_FimArm_arm_err_code(msg_);
  }

private:
  ::genie_msgs::msg::FimArm msg_;
};

class Init_FimArm_header
{
public:
  Init_FimArm_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_FimArm_fim_arm header(::genie_msgs::msg::FimArm::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_FimArm_fim_arm(msg_);
  }

private:
  ::genie_msgs::msg::FimArm msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::FimArm>()
{
  return genie_msgs::msg::builder::Init_FimArm_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__FIM_ARM__BUILDER_HPP_
