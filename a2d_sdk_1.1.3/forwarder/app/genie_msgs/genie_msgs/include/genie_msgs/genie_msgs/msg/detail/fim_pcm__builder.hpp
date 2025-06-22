// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/FimPCM.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FIM_PCM__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__FIM_PCM__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/fim_pcm__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_FimPCM_err_code
{
public:
  explicit Init_FimPCM_err_code(::genie_msgs::msg::FimPCM & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::FimPCM err_code(::genie_msgs::msg::FimPCM::_err_code_type arg)
  {
    msg_.err_code = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::FimPCM msg_;
};

class Init_FimPCM_fim_pcm
{
public:
  explicit Init_FimPCM_fim_pcm(::genie_msgs::msg::FimPCM & msg)
  : msg_(msg)
  {}
  Init_FimPCM_err_code fim_pcm(::genie_msgs::msg::FimPCM::_fim_pcm_type arg)
  {
    msg_.fim_pcm = std::move(arg);
    return Init_FimPCM_err_code(msg_);
  }

private:
  ::genie_msgs::msg::FimPCM msg_;
};

class Init_FimPCM_header
{
public:
  Init_FimPCM_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_FimPCM_fim_pcm header(::genie_msgs::msg::FimPCM::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_FimPCM_fim_pcm(msg_);
  }

private:
  ::genie_msgs::msg::FimPCM msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::FimPCM>()
{
  return genie_msgs::msg::builder::Init_FimPCM_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__FIM_PCM__BUILDER_HPP_
