// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/FaultStatus.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FAULT_STATUS__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__FAULT_STATUS__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/fault_status__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_FaultStatus_faults
{
public:
  explicit Init_FaultStatus_faults(::genie_msgs::msg::FaultStatus & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::FaultStatus faults(::genie_msgs::msg::FaultStatus::_faults_type arg)
  {
    msg_.faults = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::FaultStatus msg_;
};

class Init_FaultStatus_header
{
public:
  Init_FaultStatus_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_FaultStatus_faults header(::genie_msgs::msg::FaultStatus::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_FaultStatus_faults(msg_);
  }

private:
  ::genie_msgs::msg::FaultStatus msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::FaultStatus>()
{
  return genie_msgs::msg::builder::Init_FaultStatus_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__FAULT_STATUS__BUILDER_HPP_
