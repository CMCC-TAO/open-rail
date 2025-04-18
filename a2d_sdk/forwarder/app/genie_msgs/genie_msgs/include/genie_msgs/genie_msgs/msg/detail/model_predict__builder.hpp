// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/ModelPredict.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__MODEL_PREDICT__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__MODEL_PREDICT__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/model_predict__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_ModelPredict_trajectory_reference_time
{
public:
  explicit Init_ModelPredict_trajectory_reference_time(::genie_msgs::msg::ModelPredict & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::ModelPredict trajectory_reference_time(::genie_msgs::msg::ModelPredict::_trajectory_reference_time_type arg)
  {
    msg_.trajectory_reference_time = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::ModelPredict msg_;
};

class Init_ModelPredict_model_sleep_time
{
public:
  explicit Init_ModelPredict_model_sleep_time(::genie_msgs::msg::ModelPredict & msg)
  : msg_(msg)
  {}
  Init_ModelPredict_trajectory_reference_time model_sleep_time(::genie_msgs::msg::ModelPredict::_model_sleep_time_type arg)
  {
    msg_.model_sleep_time = std::move(arg);
    return Init_ModelPredict_trajectory_reference_time(msg_);
  }

private:
  ::genie_msgs::msg::ModelPredict msg_;
};

class Init_ModelPredict_target_joint_states
{
public:
  explicit Init_ModelPredict_target_joint_states(::genie_msgs::msg::ModelPredict & msg)
  : msg_(msg)
  {}
  Init_ModelPredict_model_sleep_time target_joint_states(::genie_msgs::msg::ModelPredict::_target_joint_states_type arg)
  {
    msg_.target_joint_states = std::move(arg);
    return Init_ModelPredict_model_sleep_time(msg_);
  }

private:
  ::genie_msgs::msg::ModelPredict msg_;
};

class Init_ModelPredict_target_poses
{
public:
  explicit Init_ModelPredict_target_poses(::genie_msgs::msg::ModelPredict & msg)
  : msg_(msg)
  {}
  Init_ModelPredict_target_joint_states target_poses(::genie_msgs::msg::ModelPredict::_target_poses_type arg)
  {
    msg_.target_poses = std::move(arg);
    return Init_ModelPredict_target_joint_states(msg_);
  }

private:
  ::genie_msgs::msg::ModelPredict msg_;
};

class Init_ModelPredict_model_output_type
{
public:
  explicit Init_ModelPredict_model_output_type(::genie_msgs::msg::ModelPredict & msg)
  : msg_(msg)
  {}
  Init_ModelPredict_target_poses model_output_type(::genie_msgs::msg::ModelPredict::_model_output_type_type arg)
  {
    msg_.model_output_type = std::move(arg);
    return Init_ModelPredict_target_poses(msg_);
  }

private:
  ::genie_msgs::msg::ModelPredict msg_;
};

class Init_ModelPredict_body_joint_positions
{
public:
  explicit Init_ModelPredict_body_joint_positions(::genie_msgs::msg::ModelPredict & msg)
  : msg_(msg)
  {}
  Init_ModelPredict_model_output_type body_joint_positions(::genie_msgs::msg::ModelPredict::_body_joint_positions_type arg)
  {
    msg_.body_joint_positions = std::move(arg);
    return Init_ModelPredict_model_output_type(msg_);
  }

private:
  ::genie_msgs::msg::ModelPredict msg_;
};

class Init_ModelPredict_body_joint_names
{
public:
  explicit Init_ModelPredict_body_joint_names(::genie_msgs::msg::ModelPredict & msg)
  : msg_(msg)
  {}
  Init_ModelPredict_body_joint_positions body_joint_names(::genie_msgs::msg::ModelPredict::_body_joint_names_type arg)
  {
    msg_.body_joint_names = std::move(arg);
    return Init_ModelPredict_body_joint_positions(msg_);
  }

private:
  ::genie_msgs::msg::ModelPredict msg_;
};

class Init_ModelPredict_header
{
public:
  Init_ModelPredict_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ModelPredict_body_joint_names header(::genie_msgs::msg::ModelPredict::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_ModelPredict_body_joint_names(msg_);
  }

private:
  ::genie_msgs::msg::ModelPredict msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::ModelPredict>()
{
  return genie_msgs::msg::builder::Init_ModelPredict_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__MODEL_PREDICT__BUILDER_HPP_
