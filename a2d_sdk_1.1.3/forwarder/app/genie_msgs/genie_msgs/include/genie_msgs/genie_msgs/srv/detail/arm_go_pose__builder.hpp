// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:srv/ArmGoPose.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__ARM_GO_POSE__BUILDER_HPP_
#define GENIE_MSGS__SRV__DETAIL__ARM_GO_POSE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/srv/detail/arm_go_pose__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_ArmGoPose_Request_block
{
public:
  explicit Init_ArmGoPose_Request_block(::genie_msgs::srv::ArmGoPose_Request & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::ArmGoPose_Request block(::genie_msgs::srv::ArmGoPose_Request::_block_type arg)
  {
    msg_.block = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::ArmGoPose_Request msg_;
};

class Init_ArmGoPose_Request_joint_states
{
public:
  explicit Init_ArmGoPose_Request_joint_states(::genie_msgs::srv::ArmGoPose_Request & msg)
  : msg_(msg)
  {}
  Init_ArmGoPose_Request_block joint_states(::genie_msgs::srv::ArmGoPose_Request::_joint_states_type arg)
  {
    msg_.joint_states = std::move(arg);
    return Init_ArmGoPose_Request_block(msg_);
  }

private:
  ::genie_msgs::srv::ArmGoPose_Request msg_;
};

class Init_ArmGoPose_Request_arm_sel
{
public:
  explicit Init_ArmGoPose_Request_arm_sel(::genie_msgs::srv::ArmGoPose_Request & msg)
  : msg_(msg)
  {}
  Init_ArmGoPose_Request_joint_states arm_sel(::genie_msgs::srv::ArmGoPose_Request::_arm_sel_type arg)
  {
    msg_.arm_sel = std::move(arg);
    return Init_ArmGoPose_Request_joint_states(msg_);
  }

private:
  ::genie_msgs::srv::ArmGoPose_Request msg_;
};

class Init_ArmGoPose_Request_header
{
public:
  Init_ArmGoPose_Request_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ArmGoPose_Request_arm_sel header(::genie_msgs::srv::ArmGoPose_Request::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_ArmGoPose_Request_arm_sel(msg_);
  }

private:
  ::genie_msgs::srv::ArmGoPose_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::ArmGoPose_Request>()
{
  return genie_msgs::srv::builder::Init_ArmGoPose_Request_header();
}

}  // namespace genie_msgs


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_ArmGoPose_Response_exec_result
{
public:
  explicit Init_ArmGoPose_Response_exec_result(::genie_msgs::srv::ArmGoPose_Response & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::ArmGoPose_Response exec_result(::genie_msgs::srv::ArmGoPose_Response::_exec_result_type arg)
  {
    msg_.exec_result = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::ArmGoPose_Response msg_;
};

class Init_ArmGoPose_Response_res_header
{
public:
  Init_ArmGoPose_Response_res_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ArmGoPose_Response_exec_result res_header(::genie_msgs::srv::ArmGoPose_Response::_res_header_type arg)
  {
    msg_.res_header = std::move(arg);
    return Init_ArmGoPose_Response_exec_result(msg_);
  }

private:
  ::genie_msgs::srv::ArmGoPose_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::ArmGoPose_Response>()
{
  return genie_msgs::srv::builder::Init_ArmGoPose_Response_res_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__SRV__DETAIL__ARM_GO_POSE__BUILDER_HPP_
