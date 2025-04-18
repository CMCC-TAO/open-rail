// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/ArmState.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__ARM_STATE__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__ARM_STATE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/arm_state__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_ArmState_system_error
{
public:
  explicit Init_ArmState_system_error(::genie_msgs::msg::ArmState & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::ArmState system_error(::genie_msgs::msg::ArmState::_system_error_type arg)
  {
    msg_.system_error = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::ArmState msg_;
};

class Init_ArmState_arm_state
{
public:
  explicit Init_ArmState_arm_state(::genie_msgs::msg::ArmState & msg)
  : msg_(msg)
  {}
  Init_ArmState_system_error arm_state(::genie_msgs::msg::ArmState::_arm_state_type arg)
  {
    msg_.arm_state = std::move(arg);
    return Init_ArmState_system_error(msg_);
  }

private:
  ::genie_msgs::msg::ArmState msg_;
};

class Init_ArmState_force_state
{
public:
  explicit Init_ArmState_force_state(::genie_msgs::msg::ArmState & msg)
  : msg_(msg)
  {}
  Init_ArmState_arm_state force_state(::genie_msgs::msg::ArmState::_force_state_type arg)
  {
    msg_.force_state = std::move(arg);
    return Init_ArmState_arm_state(msg_);
  }

private:
  ::genie_msgs::msg::ArmState msg_;
};

class Init_ArmState_force_coordinate
{
public:
  explicit Init_ArmState_force_coordinate(::genie_msgs::msg::ArmState & msg)
  : msg_(msg)
  {}
  Init_ArmState_force_state force_coordinate(::genie_msgs::msg::ArmState::_force_coordinate_type arg)
  {
    msg_.force_coordinate = std::move(arg);
    return Init_ArmState_force_state(msg_);
  }

private:
  ::genie_msgs::msg::ArmState msg_;
};

class Init_ArmState_force_data
{
public:
  explicit Init_ArmState_force_data(::genie_msgs::msg::ArmState & msg)
  : msg_(msg)
  {}
  Init_ArmState_force_coordinate force_data(::genie_msgs::msg::ArmState::_force_data_type arg)
  {
    msg_.force_data = std::move(arg);
    return Init_ArmState_force_coordinate(msg_);
  }

private:
  ::genie_msgs::msg::ArmState msg_;
};

class Init_ArmState_motor_states
{
public:
  explicit Init_ArmState_motor_states(::genie_msgs::msg::ArmState & msg)
  : msg_(msg)
  {}
  Init_ArmState_force_data motor_states(::genie_msgs::msg::ArmState::_motor_states_type arg)
  {
    msg_.motor_states = std::move(arg);
    return Init_ArmState_force_data(msg_);
  }

private:
  ::genie_msgs::msg::ArmState msg_;
};

class Init_ArmState_header
{
public:
  Init_ArmState_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ArmState_motor_states header(::genie_msgs::msg::ArmState::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_ArmState_motor_states(msg_);
  }

private:
  ::genie_msgs::msg::ArmState msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::ArmState>()
{
  return genie_msgs::msg::builder::Init_ArmState_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__ARM_STATE__BUILDER_HPP_
