// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/HeadState.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__HEAD_STATE__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__HEAD_STATE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/head_state__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_HeadState_name
{
public:
  explicit Init_HeadState_name(::genie_msgs::msg::HeadState & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::HeadState name(::genie_msgs::msg::HeadState::_name_type arg)
  {
    msg_.name = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::HeadState msg_;
};

class Init_HeadState_motor_states
{
public:
  explicit Init_HeadState_motor_states(::genie_msgs::msg::HeadState & msg)
  : msg_(msg)
  {}
  Init_HeadState_name motor_states(::genie_msgs::msg::HeadState::_motor_states_type arg)
  {
    msg_.motor_states = std::move(arg);
    return Init_HeadState_name(msg_);
  }

private:
  ::genie_msgs::msg::HeadState msg_;
};

class Init_HeadState_header
{
public:
  Init_HeadState_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_HeadState_motor_states header(::genie_msgs::msg::HeadState::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_HeadState_motor_states(msg_);
  }

private:
  ::genie_msgs::msg::HeadState msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::HeadState>()
{
  return genie_msgs::msg::builder::Init_HeadState_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__HEAD_STATE__BUILDER_HPP_
