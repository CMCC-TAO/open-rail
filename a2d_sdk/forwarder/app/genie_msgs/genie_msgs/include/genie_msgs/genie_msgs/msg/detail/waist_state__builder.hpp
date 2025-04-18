// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/WaistState.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__WAIST_STATE__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__WAIST_STATE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/waist_state__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_WaistState_name
{
public:
  explicit Init_WaistState_name(::genie_msgs::msg::WaistState & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::WaistState name(::genie_msgs::msg::WaistState::_name_type arg)
  {
    msg_.name = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::WaistState msg_;
};

class Init_WaistState_motor_states
{
public:
  explicit Init_WaistState_motor_states(::genie_msgs::msg::WaistState & msg)
  : msg_(msg)
  {}
  Init_WaistState_name motor_states(::genie_msgs::msg::WaistState::_motor_states_type arg)
  {
    msg_.motor_states = std::move(arg);
    return Init_WaistState_name(msg_);
  }

private:
  ::genie_msgs::msg::WaistState msg_;
};

class Init_WaistState_header
{
public:
  Init_WaistState_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_WaistState_motor_states header(::genie_msgs::msg::WaistState::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_WaistState_motor_states(msg_);
  }

private:
  ::genie_msgs::msg::WaistState msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::WaistState>()
{
  return genie_msgs::msg::builder::Init_WaistState_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__WAIST_STATE__BUILDER_HPP_
