// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/FimAGV.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FIM_AGV__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__FIM_AGV__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/fim_agv__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_FimAGV_agv_err_code
{
public:
  explicit Init_FimAGV_agv_err_code(::genie_msgs::msg::FimAGV & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::FimAGV agv_err_code(::genie_msgs::msg::FimAGV::_agv_err_code_type arg)
  {
    msg_.agv_err_code = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::FimAGV msg_;
};

class Init_FimAGV_fim_agv
{
public:
  explicit Init_FimAGV_fim_agv(::genie_msgs::msg::FimAGV & msg)
  : msg_(msg)
  {}
  Init_FimAGV_agv_err_code fim_agv(::genie_msgs::msg::FimAGV::_fim_agv_type arg)
  {
    msg_.fim_agv = std::move(arg);
    return Init_FimAGV_agv_err_code(msg_);
  }

private:
  ::genie_msgs::msg::FimAGV msg_;
};

class Init_FimAGV_header
{
public:
  Init_FimAGV_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_FimAGV_fim_agv header(::genie_msgs::msg::FimAGV::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_FimAGV_fim_agv(msg_);
  }

private:
  ::genie_msgs::msg::FimAGV msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::FimAGV>()
{
  return genie_msgs::msg::builder::Init_FimAGV_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__FIM_AGV__BUILDER_HPP_
