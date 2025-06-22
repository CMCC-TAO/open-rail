// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/TargetStation.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__TARGET_STATION__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__TARGET_STATION__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/target_station__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_TargetStation_status
{
public:
  explicit Init_TargetStation_status(::genie_msgs::msg::TargetStation & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::TargetStation status(::genie_msgs::msg::TargetStation::_status_type arg)
  {
    msg_.status = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::TargetStation msg_;
};

class Init_TargetStation_header
{
public:
  Init_TargetStation_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_TargetStation_status header(::genie_msgs::msg::TargetStation::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_TargetStation_status(msg_);
  }

private:
  ::genie_msgs::msg::TargetStation msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::TargetStation>()
{
  return genie_msgs::msg::builder::Init_TargetStation_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__TARGET_STATION__BUILDER_HPP_
