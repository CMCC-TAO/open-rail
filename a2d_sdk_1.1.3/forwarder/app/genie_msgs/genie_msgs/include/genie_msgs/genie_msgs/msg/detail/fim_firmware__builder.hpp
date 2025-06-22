// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/FimFirmware.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FIM_FIRMWARE__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__FIM_FIRMWARE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/fim_firmware__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_FimFirmware_err_code_byte
{
public:
  explicit Init_FimFirmware_err_code_byte(::genie_msgs::msg::FimFirmware & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::FimFirmware err_code_byte(::genie_msgs::msg::FimFirmware::_err_code_byte_type arg)
  {
    msg_.err_code_byte = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::FimFirmware msg_;
};

class Init_FimFirmware_fim_fw
{
public:
  explicit Init_FimFirmware_fim_fw(::genie_msgs::msg::FimFirmware & msg)
  : msg_(msg)
  {}
  Init_FimFirmware_err_code_byte fim_fw(::genie_msgs::msg::FimFirmware::_fim_fw_type arg)
  {
    msg_.fim_fw = std::move(arg);
    return Init_FimFirmware_err_code_byte(msg_);
  }

private:
  ::genie_msgs::msg::FimFirmware msg_;
};

class Init_FimFirmware_header
{
public:
  Init_FimFirmware_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_FimFirmware_fim_fw header(::genie_msgs::msg::FimFirmware::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_FimFirmware_fim_fw(msg_);
  }

private:
  ::genie_msgs::msg::FimFirmware msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::FimFirmware>()
{
  return genie_msgs::msg::builder::Init_FimFirmware_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__FIM_FIRMWARE__BUILDER_HPP_
