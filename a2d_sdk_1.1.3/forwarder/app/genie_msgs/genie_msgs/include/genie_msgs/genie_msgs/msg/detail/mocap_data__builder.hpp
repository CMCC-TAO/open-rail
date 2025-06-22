// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/MocapData.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__MOCAP_DATA__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__MOCAP_DATA__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/mocap_data__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_MocapData_mocap_joint_states
{
public:
  explicit Init_MocapData_mocap_joint_states(::genie_msgs::msg::MocapData & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::MocapData mocap_joint_states(::genie_msgs::msg::MocapData::_mocap_joint_states_type arg)
  {
    msg_.mocap_joint_states = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::MocapData msg_;
};

class Init_MocapData_err_code
{
public:
  explicit Init_MocapData_err_code(::genie_msgs::msg::MocapData & msg)
  : msg_(msg)
  {}
  Init_MocapData_mocap_joint_states err_code(::genie_msgs::msg::MocapData::_err_code_type arg)
  {
    msg_.err_code = std::move(arg);
    return Init_MocapData_mocap_joint_states(msg_);
  }

private:
  ::genie_msgs::msg::MocapData msg_;
};

class Init_MocapData_status
{
public:
  explicit Init_MocapData_status(::genie_msgs::msg::MocapData & msg)
  : msg_(msg)
  {}
  Init_MocapData_err_code status(::genie_msgs::msg::MocapData::_status_type arg)
  {
    msg_.status = std::move(arg);
    return Init_MocapData_err_code(msg_);
  }

private:
  ::genie_msgs::msg::MocapData msg_;
};

class Init_MocapData_header
{
public:
  Init_MocapData_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_MocapData_status header(::genie_msgs::msg::MocapData::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_MocapData_status(msg_);
  }

private:
  ::genie_msgs::msg::MocapData msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::MocapData>()
{
  return genie_msgs::msg::builder::Init_MocapData_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__MOCAP_DATA__BUILDER_HPP_
