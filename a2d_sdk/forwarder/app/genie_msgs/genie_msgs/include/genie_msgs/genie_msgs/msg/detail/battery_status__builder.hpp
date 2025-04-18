// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/BatteryStatus.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__BATTERY_STATUS__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__BATTERY_STATUS__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/battery_status__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_BatteryStatus_status
{
public:
  explicit Init_BatteryStatus_status(::genie_msgs::msg::BatteryStatus & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::BatteryStatus status(::genie_msgs::msg::BatteryStatus::_status_type arg)
  {
    msg_.status = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::BatteryStatus msg_;
};

class Init_BatteryStatus_temperature
{
public:
  explicit Init_BatteryStatus_temperature(::genie_msgs::msg::BatteryStatus & msg)
  : msg_(msg)
  {}
  Init_BatteryStatus_status temperature(::genie_msgs::msg::BatteryStatus::_temperature_type arg)
  {
    msg_.temperature = std::move(arg);
    return Init_BatteryStatus_status(msg_);
  }

private:
  ::genie_msgs::msg::BatteryStatus msg_;
};

class Init_BatteryStatus_capacity
{
public:
  explicit Init_BatteryStatus_capacity(::genie_msgs::msg::BatteryStatus & msg)
  : msg_(msg)
  {}
  Init_BatteryStatus_temperature capacity(::genie_msgs::msg::BatteryStatus::_capacity_type arg)
  {
    msg_.capacity = std::move(arg);
    return Init_BatteryStatus_temperature(msg_);
  }

private:
  ::genie_msgs::msg::BatteryStatus msg_;
};

class Init_BatteryStatus_current
{
public:
  explicit Init_BatteryStatus_current(::genie_msgs::msg::BatteryStatus & msg)
  : msg_(msg)
  {}
  Init_BatteryStatus_capacity current(::genie_msgs::msg::BatteryStatus::_current_type arg)
  {
    msg_.current = std::move(arg);
    return Init_BatteryStatus_capacity(msg_);
  }

private:
  ::genie_msgs::msg::BatteryStatus msg_;
};

class Init_BatteryStatus_voltage
{
public:
  explicit Init_BatteryStatus_voltage(::genie_msgs::msg::BatteryStatus & msg)
  : msg_(msg)
  {}
  Init_BatteryStatus_current voltage(::genie_msgs::msg::BatteryStatus::_voltage_type arg)
  {
    msg_.voltage = std::move(arg);
    return Init_BatteryStatus_current(msg_);
  }

private:
  ::genie_msgs::msg::BatteryStatus msg_;
};

class Init_BatteryStatus_energy
{
public:
  explicit Init_BatteryStatus_energy(::genie_msgs::msg::BatteryStatus & msg)
  : msg_(msg)
  {}
  Init_BatteryStatus_voltage energy(::genie_msgs::msg::BatteryStatus::_energy_type arg)
  {
    msg_.energy = std::move(arg);
    return Init_BatteryStatus_voltage(msg_);
  }

private:
  ::genie_msgs::msg::BatteryStatus msg_;
};

class Init_BatteryStatus_header
{
public:
  Init_BatteryStatus_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_BatteryStatus_energy header(::genie_msgs::msg::BatteryStatus::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_BatteryStatus_energy(msg_);
  }

private:
  ::genie_msgs::msg::BatteryStatus msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::BatteryStatus>()
{
  return genie_msgs::msg::builder::Init_BatteryStatus_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__BATTERY_STATUS__BUILDER_HPP_
