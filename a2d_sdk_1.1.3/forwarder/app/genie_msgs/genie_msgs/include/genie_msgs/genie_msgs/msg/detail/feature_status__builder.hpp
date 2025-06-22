// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/FeatureStatus.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FEATURE_STATUS__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__FEATURE_STATUS__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/feature_status__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_FeatureStatus_feature_status
{
public:
  explicit Init_FeatureStatus_feature_status(::genie_msgs::msg::FeatureStatus & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::FeatureStatus feature_status(::genie_msgs::msg::FeatureStatus::_feature_status_type arg)
  {
    msg_.feature_status = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::FeatureStatus msg_;
};

class Init_FeatureStatus_work_mode
{
public:
  explicit Init_FeatureStatus_work_mode(::genie_msgs::msg::FeatureStatus & msg)
  : msg_(msg)
  {}
  Init_FeatureStatus_feature_status work_mode(::genie_msgs::msg::FeatureStatus::_work_mode_type arg)
  {
    msg_.work_mode = std::move(arg);
    return Init_FeatureStatus_feature_status(msg_);
  }

private:
  ::genie_msgs::msg::FeatureStatus msg_;
};

class Init_FeatureStatus_header
{
public:
  Init_FeatureStatus_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_FeatureStatus_work_mode header(::genie_msgs::msg::FeatureStatus::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_FeatureStatus_work_mode(msg_);
  }

private:
  ::genie_msgs::msg::FeatureStatus msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::FeatureStatus>()
{
  return genie_msgs::msg::builder::Init_FeatureStatus_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__FEATURE_STATUS__BUILDER_HPP_
