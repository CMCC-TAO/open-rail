// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/FimCamera.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FIM_CAMERA__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__FIM_CAMERA__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/fim_camera__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_FimCamera_err_code
{
public:
  explicit Init_FimCamera_err_code(::genie_msgs::msg::FimCamera & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::FimCamera err_code(::genie_msgs::msg::FimCamera::_err_code_type arg)
  {
    msg_.err_code = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::FimCamera msg_;
};

class Init_FimCamera_camera_name
{
public:
  explicit Init_FimCamera_camera_name(::genie_msgs::msg::FimCamera & msg)
  : msg_(msg)
  {}
  Init_FimCamera_err_code camera_name(::genie_msgs::msg::FimCamera::_camera_name_type arg)
  {
    msg_.camera_name = std::move(arg);
    return Init_FimCamera_err_code(msg_);
  }

private:
  ::genie_msgs::msg::FimCamera msg_;
};

class Init_FimCamera_fim_camera
{
public:
  explicit Init_FimCamera_fim_camera(::genie_msgs::msg::FimCamera & msg)
  : msg_(msg)
  {}
  Init_FimCamera_camera_name fim_camera(::genie_msgs::msg::FimCamera::_fim_camera_type arg)
  {
    msg_.fim_camera = std::move(arg);
    return Init_FimCamera_camera_name(msg_);
  }

private:
  ::genie_msgs::msg::FimCamera msg_;
};

class Init_FimCamera_header
{
public:
  Init_FimCamera_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_FimCamera_fim_camera header(::genie_msgs::msg::FimCamera::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_FimCamera_fim_camera(msg_);
  }

private:
  ::genie_msgs::msg::FimCamera msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::FimCamera>()
{
  return genie_msgs::msg::builder::Init_FimCamera_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__FIM_CAMERA__BUILDER_HPP_
