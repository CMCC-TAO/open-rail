// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/MocapJointState.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__MOCAP_JOINT_STATE__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__MOCAP_JOINT_STATE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/mocap_joint_state__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_MocapJointState_orientation
{
public:
  explicit Init_MocapJointState_orientation(::genie_msgs::msg::MocapJointState & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::MocapJointState orientation(::genie_msgs::msg::MocapJointState::_orientation_type arg)
  {
    msg_.orientation = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::MocapJointState msg_;
};

class Init_MocapJointState_position
{
public:
  explicit Init_MocapJointState_position(::genie_msgs::msg::MocapJointState & msg)
  : msg_(msg)
  {}
  Init_MocapJointState_orientation position(::genie_msgs::msg::MocapJointState::_position_type arg)
  {
    msg_.position = std::move(arg);
    return Init_MocapJointState_orientation(msg_);
  }

private:
  ::genie_msgs::msg::MocapJointState msg_;
};

class Init_MocapJointState_err_code
{
public:
  explicit Init_MocapJointState_err_code(::genie_msgs::msg::MocapJointState & msg)
  : msg_(msg)
  {}
  Init_MocapJointState_position err_code(::genie_msgs::msg::MocapJointState::_err_code_type arg)
  {
    msg_.err_code = std::move(arg);
    return Init_MocapJointState_position(msg_);
  }

private:
  ::genie_msgs::msg::MocapJointState msg_;
};

class Init_MocapJointState_status
{
public:
  explicit Init_MocapJointState_status(::genie_msgs::msg::MocapJointState & msg)
  : msg_(msg)
  {}
  Init_MocapJointState_err_code status(::genie_msgs::msg::MocapJointState::_status_type arg)
  {
    msg_.status = std::move(arg);
    return Init_MocapJointState_err_code(msg_);
  }

private:
  ::genie_msgs::msg::MocapJointState msg_;
};

class Init_MocapJointState_id
{
public:
  explicit Init_MocapJointState_id(::genie_msgs::msg::MocapJointState & msg)
  : msg_(msg)
  {}
  Init_MocapJointState_status id(::genie_msgs::msg::MocapJointState::_id_type arg)
  {
    msg_.id = std::move(arg);
    return Init_MocapJointState_status(msg_);
  }

private:
  ::genie_msgs::msg::MocapJointState msg_;
};

class Init_MocapJointState_name
{
public:
  Init_MocapJointState_name()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_MocapJointState_id name(::genie_msgs::msg::MocapJointState::_name_type arg)
  {
    msg_.name = std::move(arg);
    return Init_MocapJointState_id(msg_);
  }

private:
  ::genie_msgs::msg::MocapJointState msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::MocapJointState>()
{
  return genie_msgs::msg::builder::Init_MocapJointState_name();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__MOCAP_JOINT_STATE__BUILDER_HPP_
