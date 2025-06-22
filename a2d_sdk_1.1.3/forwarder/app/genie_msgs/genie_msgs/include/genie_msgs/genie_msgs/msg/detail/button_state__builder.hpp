// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/ButtonState.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__BUTTON_STATE__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__BUTTON_STATE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/button_state__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_ButtonState_pressure
{
public:
  explicit Init_ButtonState_pressure(::genie_msgs::msg::ButtonState & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::ButtonState pressure(::genie_msgs::msg::ButtonState::_pressure_type arg)
  {
    msg_.pressure = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::ButtonState msg_;
};

class Init_ButtonState_is_pressed
{
public:
  Init_ButtonState_is_pressed()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ButtonState_pressure is_pressed(::genie_msgs::msg::ButtonState::_is_pressed_type arg)
  {
    msg_.is_pressed = std::move(arg);
    return Init_ButtonState_pressure(msg_);
  }

private:
  ::genie_msgs::msg::ButtonState msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::ButtonState>()
{
  return genie_msgs::msg::builder::Init_ButtonState_is_pressed();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__BUTTON_STATE__BUILDER_HPP_
