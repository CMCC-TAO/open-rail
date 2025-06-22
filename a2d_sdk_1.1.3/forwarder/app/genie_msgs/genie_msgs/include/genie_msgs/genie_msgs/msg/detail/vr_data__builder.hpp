// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/VRData.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__VR_DATA__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__VR_DATA__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/vr_data__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_VRData_vr_controller_states
{
public:
  explicit Init_VRData_vr_controller_states(::genie_msgs::msg::VRData & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::VRData vr_controller_states(::genie_msgs::msg::VRData::_vr_controller_states_type arg)
  {
    msg_.vr_controller_states = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::VRData msg_;
};

class Init_VRData_err_code
{
public:
  explicit Init_VRData_err_code(::genie_msgs::msg::VRData & msg)
  : msg_(msg)
  {}
  Init_VRData_vr_controller_states err_code(::genie_msgs::msg::VRData::_err_code_type arg)
  {
    msg_.err_code = std::move(arg);
    return Init_VRData_vr_controller_states(msg_);
  }

private:
  ::genie_msgs::msg::VRData msg_;
};

class Init_VRData_status
{
public:
  explicit Init_VRData_status(::genie_msgs::msg::VRData & msg)
  : msg_(msg)
  {}
  Init_VRData_err_code status(::genie_msgs::msg::VRData::_status_type arg)
  {
    msg_.status = std::move(arg);
    return Init_VRData_err_code(msg_);
  }

private:
  ::genie_msgs::msg::VRData msg_;
};

class Init_VRData_header
{
public:
  Init_VRData_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_VRData_status header(::genie_msgs::msg::VRData::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_VRData_status(msg_);
  }

private:
  ::genie_msgs::msg::VRData msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::VRData>()
{
  return genie_msgs::msg::builder::Init_VRData_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__VR_DATA__BUILDER_HPP_
