// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:srv/ArmInitPose.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__ARM_INIT_POSE__BUILDER_HPP_
#define GENIE_MSGS__SRV__DETAIL__ARM_INIT_POSE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/srv/detail/arm_init_pose__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_ArmInitPose_Request_block
{
public:
  explicit Init_ArmInitPose_Request_block(::genie_msgs::srv::ArmInitPose_Request & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::ArmInitPose_Request block(::genie_msgs::srv::ArmInitPose_Request::_block_type arg)
  {
    msg_.block = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::ArmInitPose_Request msg_;
};

class Init_ArmInitPose_Request_reset_mode
{
public:
  explicit Init_ArmInitPose_Request_reset_mode(::genie_msgs::srv::ArmInitPose_Request & msg)
  : msg_(msg)
  {}
  Init_ArmInitPose_Request_block reset_mode(::genie_msgs::srv::ArmInitPose_Request::_reset_mode_type arg)
  {
    msg_.reset_mode = std::move(arg);
    return Init_ArmInitPose_Request_block(msg_);
  }

private:
  ::genie_msgs::srv::ArmInitPose_Request msg_;
};

class Init_ArmInitPose_Request_arm_sel
{
public:
  explicit Init_ArmInitPose_Request_arm_sel(::genie_msgs::srv::ArmInitPose_Request & msg)
  : msg_(msg)
  {}
  Init_ArmInitPose_Request_reset_mode arm_sel(::genie_msgs::srv::ArmInitPose_Request::_arm_sel_type arg)
  {
    msg_.arm_sel = std::move(arg);
    return Init_ArmInitPose_Request_reset_mode(msg_);
  }

private:
  ::genie_msgs::srv::ArmInitPose_Request msg_;
};

class Init_ArmInitPose_Request_header
{
public:
  Init_ArmInitPose_Request_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ArmInitPose_Request_arm_sel header(::genie_msgs::srv::ArmInitPose_Request::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_ArmInitPose_Request_arm_sel(msg_);
  }

private:
  ::genie_msgs::srv::ArmInitPose_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::ArmInitPose_Request>()
{
  return genie_msgs::srv::builder::Init_ArmInitPose_Request_header();
}

}  // namespace genie_msgs


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_ArmInitPose_Response_exec_result
{
public:
  explicit Init_ArmInitPose_Response_exec_result(::genie_msgs::srv::ArmInitPose_Response & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::ArmInitPose_Response exec_result(::genie_msgs::srv::ArmInitPose_Response::_exec_result_type arg)
  {
    msg_.exec_result = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::ArmInitPose_Response msg_;
};

class Init_ArmInitPose_Response_res_header
{
public:
  Init_ArmInitPose_Response_res_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ArmInitPose_Response_exec_result res_header(::genie_msgs::srv::ArmInitPose_Response::_res_header_type arg)
  {
    msg_.res_header = std::move(arg);
    return Init_ArmInitPose_Response_exec_result(msg_);
  }

private:
  ::genie_msgs::srv::ArmInitPose_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::ArmInitPose_Response>()
{
  return genie_msgs::srv::builder::Init_ArmInitPose_Response_res_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__SRV__DETAIL__ARM_INIT_POSE__BUILDER_HPP_
