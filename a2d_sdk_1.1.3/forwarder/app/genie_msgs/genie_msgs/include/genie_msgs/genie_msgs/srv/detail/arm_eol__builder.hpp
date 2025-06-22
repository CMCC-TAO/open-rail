// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:srv/ArmEOL.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__ARM_EOL__BUILDER_HPP_
#define GENIE_MSGS__SRV__DETAIL__ARM_EOL__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/srv/detail/arm_eol__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_ArmEOL_Request_arm_sel
{
public:
  explicit Init_ArmEOL_Request_arm_sel(::genie_msgs::srv::ArmEOL_Request & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::ArmEOL_Request arm_sel(::genie_msgs::srv::ArmEOL_Request::_arm_sel_type arg)
  {
    msg_.arm_sel = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::ArmEOL_Request msg_;
};

class Init_ArmEOL_Request_header
{
public:
  Init_ArmEOL_Request_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ArmEOL_Request_arm_sel header(::genie_msgs::srv::ArmEOL_Request::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_ArmEOL_Request_arm_sel(msg_);
  }

private:
  ::genie_msgs::srv::ArmEOL_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::ArmEOL_Request>()
{
  return genie_msgs::srv::builder::Init_ArmEOL_Request_header();
}

}  // namespace genie_msgs


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_ArmEOL_Response_exec_result
{
public:
  explicit Init_ArmEOL_Response_exec_result(::genie_msgs::srv::ArmEOL_Response & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::ArmEOL_Response exec_result(::genie_msgs::srv::ArmEOL_Response::_exec_result_type arg)
  {
    msg_.exec_result = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::ArmEOL_Response msg_;
};

class Init_ArmEOL_Response_res_header
{
public:
  Init_ArmEOL_Response_res_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ArmEOL_Response_exec_result res_header(::genie_msgs::srv::ArmEOL_Response::_res_header_type arg)
  {
    msg_.res_header = std::move(arg);
    return Init_ArmEOL_Response_exec_result(msg_);
  }

private:
  ::genie_msgs::srv::ArmEOL_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::ArmEOL_Response>()
{
  return genie_msgs::srv::builder::Init_ArmEOL_Response_res_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__SRV__DETAIL__ARM_EOL__BUILDER_HPP_
