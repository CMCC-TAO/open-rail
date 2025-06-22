// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/Retarget.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__RETARGET__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__RETARGET__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/retarget__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_Retarget_body_joint_positions
{
public:
  explicit Init_Retarget_body_joint_positions(::genie_msgs::msg::Retarget & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::Retarget body_joint_positions(::genie_msgs::msg::Retarget::_body_joint_positions_type arg)
  {
    msg_.body_joint_positions = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::Retarget msg_;
};

class Init_Retarget_body_joint_names
{
public:
  explicit Init_Retarget_body_joint_names(::genie_msgs::msg::Retarget & msg)
  : msg_(msg)
  {}
  Init_Retarget_body_joint_positions body_joint_names(::genie_msgs::msg::Retarget::_body_joint_names_type arg)
  {
    msg_.body_joint_names = std::move(arg);
    return Init_Retarget_body_joint_positions(msg_);
  }

private:
  ::genie_msgs::msg::Retarget msg_;
};

class Init_Retarget_right_upper_arm
{
public:
  explicit Init_Retarget_right_upper_arm(::genie_msgs::msg::Retarget & msg)
  : msg_(msg)
  {}
  Init_Retarget_body_joint_names right_upper_arm(::genie_msgs::msg::Retarget::_right_upper_arm_type arg)
  {
    msg_.right_upper_arm = std::move(arg);
    return Init_Retarget_body_joint_names(msg_);
  }

private:
  ::genie_msgs::msg::Retarget msg_;
};

class Init_Retarget_left_upper_arm
{
public:
  explicit Init_Retarget_left_upper_arm(::genie_msgs::msg::Retarget & msg)
  : msg_(msg)
  {}
  Init_Retarget_right_upper_arm left_upper_arm(::genie_msgs::msg::Retarget::_left_upper_arm_type arg)
  {
    msg_.left_upper_arm = std::move(arg);
    return Init_Retarget_right_upper_arm(msg_);
  }

private:
  ::genie_msgs::msg::Retarget msg_;
};

class Init_Retarget_right_ee_pose
{
public:
  explicit Init_Retarget_right_ee_pose(::genie_msgs::msg::Retarget & msg)
  : msg_(msg)
  {}
  Init_Retarget_left_upper_arm right_ee_pose(::genie_msgs::msg::Retarget::_right_ee_pose_type arg)
  {
    msg_.right_ee_pose = std::move(arg);
    return Init_Retarget_left_upper_arm(msg_);
  }

private:
  ::genie_msgs::msg::Retarget msg_;
};

class Init_Retarget_left_ee_pose
{
public:
  explicit Init_Retarget_left_ee_pose(::genie_msgs::msg::Retarget & msg)
  : msg_(msg)
  {}
  Init_Retarget_right_ee_pose left_ee_pose(::genie_msgs::msg::Retarget::_left_ee_pose_type arg)
  {
    msg_.left_ee_pose = std::move(arg);
    return Init_Retarget_right_ee_pose(msg_);
  }

private:
  ::genie_msgs::msg::Retarget msg_;
};

class Init_Retarget_device
{
public:
  explicit Init_Retarget_device(::genie_msgs::msg::Retarget & msg)
  : msg_(msg)
  {}
  Init_Retarget_left_ee_pose device(::genie_msgs::msg::Retarget::_device_type arg)
  {
    msg_.device = std::move(arg);
    return Init_Retarget_left_ee_pose(msg_);
  }

private:
  ::genie_msgs::msg::Retarget msg_;
};

class Init_Retarget_group_body
{
public:
  explicit Init_Retarget_group_body(::genie_msgs::msg::Retarget & msg)
  : msg_(msg)
  {}
  Init_Retarget_device group_body(::genie_msgs::msg::Retarget::_group_body_type arg)
  {
    msg_.group_body = std::move(arg);
    return Init_Retarget_device(msg_);
  }

private:
  ::genie_msgs::msg::Retarget msg_;
};

class Init_Retarget_group_arms
{
public:
  explicit Init_Retarget_group_arms(::genie_msgs::msg::Retarget & msg)
  : msg_(msg)
  {}
  Init_Retarget_group_body group_arms(::genie_msgs::msg::Retarget::_group_arms_type arg)
  {
    msg_.group_arms = std::move(arg);
    return Init_Retarget_group_body(msg_);
  }

private:
  ::genie_msgs::msg::Retarget msg_;
};

class Init_Retarget_header
{
public:
  Init_Retarget_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_Retarget_group_arms header(::genie_msgs::msg::Retarget::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_Retarget_group_arms(msg_);
  }

private:
  ::genie_msgs::msg::Retarget msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::Retarget>()
{
  return genie_msgs::msg::builder::Init_Retarget_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__RETARGET__BUILDER_HPP_
