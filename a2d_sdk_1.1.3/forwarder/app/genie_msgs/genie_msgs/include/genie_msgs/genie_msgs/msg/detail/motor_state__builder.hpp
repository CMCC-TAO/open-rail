// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/MotorState.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__MOTOR_STATE__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__MOTOR_STATE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/motor_state__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_MotorState_err_code
{
public:
  explicit Init_MotorState_err_code(::genie_msgs::msg::MotorState & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::MotorState err_code(::genie_msgs::msg::MotorState::_err_code_type arg)
  {
    msg_.err_code = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::MotorState msg_;
};

class Init_MotorState_status
{
public:
  explicit Init_MotorState_status(::genie_msgs::msg::MotorState & msg)
  : msg_(msg)
  {}
  Init_MotorState_err_code status(::genie_msgs::msg::MotorState::_status_type arg)
  {
    msg_.status = std::move(arg);
    return Init_MotorState_err_code(msg_);
  }

private:
  ::genie_msgs::msg::MotorState msg_;
};

class Init_MotorState_temperature
{
public:
  explicit Init_MotorState_temperature(::genie_msgs::msg::MotorState & msg)
  : msg_(msg)
  {}
  Init_MotorState_status temperature(::genie_msgs::msg::MotorState::_temperature_type arg)
  {
    msg_.temperature = std::move(arg);
    return Init_MotorState_status(msg_);
  }

private:
  ::genie_msgs::msg::MotorState msg_;
};

class Init_MotorState_voltage
{
public:
  explicit Init_MotorState_voltage(::genie_msgs::msg::MotorState & msg)
  : msg_(msg)
  {}
  Init_MotorState_temperature voltage(::genie_msgs::msg::MotorState::_voltage_type arg)
  {
    msg_.voltage = std::move(arg);
    return Init_MotorState_temperature(msg_);
  }

private:
  ::genie_msgs::msg::MotorState msg_;
};

class Init_MotorState_current
{
public:
  explicit Init_MotorState_current(::genie_msgs::msg::MotorState & msg)
  : msg_(msg)
  {}
  Init_MotorState_voltage current(::genie_msgs::msg::MotorState::_current_type arg)
  {
    msg_.current = std::move(arg);
    return Init_MotorState_voltage(msg_);
  }

private:
  ::genie_msgs::msg::MotorState msg_;
};

class Init_MotorState_effort
{
public:
  explicit Init_MotorState_effort(::genie_msgs::msg::MotorState & msg)
  : msg_(msg)
  {}
  Init_MotorState_current effort(::genie_msgs::msg::MotorState::_effort_type arg)
  {
    msg_.effort = std::move(arg);
    return Init_MotorState_current(msg_);
  }

private:
  ::genie_msgs::msg::MotorState msg_;
};

class Init_MotorState_velocity
{
public:
  explicit Init_MotorState_velocity(::genie_msgs::msg::MotorState & msg)
  : msg_(msg)
  {}
  Init_MotorState_effort velocity(::genie_msgs::msg::MotorState::_velocity_type arg)
  {
    msg_.velocity = std::move(arg);
    return Init_MotorState_effort(msg_);
  }

private:
  ::genie_msgs::msg::MotorState msg_;
};

class Init_MotorState_position
{
public:
  explicit Init_MotorState_position(::genie_msgs::msg::MotorState & msg)
  : msg_(msg)
  {}
  Init_MotorState_velocity position(::genie_msgs::msg::MotorState::_position_type arg)
  {
    msg_.position = std::move(arg);
    return Init_MotorState_velocity(msg_);
  }

private:
  ::genie_msgs::msg::MotorState msg_;
};

class Init_MotorState_enable
{
public:
  explicit Init_MotorState_enable(::genie_msgs::msg::MotorState & msg)
  : msg_(msg)
  {}
  Init_MotorState_position enable(::genie_msgs::msg::MotorState::_enable_type arg)
  {
    msg_.enable = std::move(arg);
    return Init_MotorState_position(msg_);
  }

private:
  ::genie_msgs::msg::MotorState msg_;
};

class Init_MotorState_id
{
public:
  Init_MotorState_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_MotorState_enable id(::genie_msgs::msg::MotorState::_id_type arg)
  {
    msg_.id = std::move(arg);
    return Init_MotorState_enable(msg_);
  }

private:
  ::genie_msgs::msg::MotorState msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::MotorState>()
{
  return genie_msgs::msg::builder::Init_MotorState_id();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__MOTOR_STATE__BUILDER_HPP_
