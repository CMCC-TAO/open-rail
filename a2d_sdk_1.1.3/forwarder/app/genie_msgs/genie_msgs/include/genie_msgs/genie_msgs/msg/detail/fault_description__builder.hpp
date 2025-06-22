// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/FaultDescription.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FAULT_DESCRIPTION__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__FAULT_DESCRIPTION__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/fault_description__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_FaultDescription_error_code
{
public:
  explicit Init_FaultDescription_error_code(::genie_msgs::msg::FaultDescription & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::FaultDescription error_code(::genie_msgs::msg::FaultDescription::_error_code_type arg)
  {
    msg_.error_code = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::FaultDescription msg_;
};

class Init_FaultDescription_error_id
{
public:
  Init_FaultDescription_error_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_FaultDescription_error_code error_id(::genie_msgs::msg::FaultDescription::_error_id_type arg)
  {
    msg_.error_id = std::move(arg);
    return Init_FaultDescription_error_code(msg_);
  }

private:
  ::genie_msgs::msg::FaultDescription msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::FaultDescription>()
{
  return genie_msgs::msg::builder::Init_FaultDescription_error_id();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__FAULT_DESCRIPTION__BUILDER_HPP_
