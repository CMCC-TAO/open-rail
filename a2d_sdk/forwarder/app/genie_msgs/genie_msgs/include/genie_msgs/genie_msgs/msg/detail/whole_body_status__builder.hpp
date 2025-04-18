// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/WholeBodyStatus.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__WHOLE_BODY_STATUS__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__WHOLE_BODY_STATUS__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/whole_body_status__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_WholeBodyStatus_chassis_error
{
public:
  explicit Init_WholeBodyStatus_chassis_error(::genie_msgs::msg::WholeBodyStatus & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::WholeBodyStatus chassis_error(::genie_msgs::msg::WholeBodyStatus::_chassis_error_type arg)
  {
    msg_.chassis_error = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::WholeBodyStatus msg_;
};

class Init_WholeBodyStatus_neck_error
{
public:
  explicit Init_WholeBodyStatus_neck_error(::genie_msgs::msg::WholeBodyStatus & msg)
  : msg_(msg)
  {}
  Init_WholeBodyStatus_chassis_error neck_error(::genie_msgs::msg::WholeBodyStatus::_neck_error_type arg)
  {
    msg_.neck_error = std::move(arg);
    return Init_WholeBodyStatus_chassis_error(msg_);
  }

private:
  ::genie_msgs::msg::WholeBodyStatus msg_;
};

class Init_WholeBodyStatus_lift_error
{
public:
  explicit Init_WholeBodyStatus_lift_error(::genie_msgs::msg::WholeBodyStatus & msg)
  : msg_(msg)
  {}
  Init_WholeBodyStatus_neck_error lift_error(::genie_msgs::msg::WholeBodyStatus::_lift_error_type arg)
  {
    msg_.lift_error = std::move(arg);
    return Init_WholeBodyStatus_neck_error(msg_);
  }

private:
  ::genie_msgs::msg::WholeBodyStatus msg_;
};

class Init_WholeBodyStatus_waist_error
{
public:
  explicit Init_WholeBodyStatus_waist_error(::genie_msgs::msg::WholeBodyStatus & msg)
  : msg_(msg)
  {}
  Init_WholeBodyStatus_lift_error waist_error(::genie_msgs::msg::WholeBodyStatus::_waist_error_type arg)
  {
    msg_.waist_error = std::move(arg);
    return Init_WholeBodyStatus_lift_error(msg_);
  }

private:
  ::genie_msgs::msg::WholeBodyStatus msg_;
};

class Init_WholeBodyStatus_left_end_error
{
public:
  explicit Init_WholeBodyStatus_left_end_error(::genie_msgs::msg::WholeBodyStatus & msg)
  : msg_(msg)
  {}
  Init_WholeBodyStatus_waist_error left_end_error(::genie_msgs::msg::WholeBodyStatus::_left_end_error_type arg)
  {
    msg_.left_end_error = std::move(arg);
    return Init_WholeBodyStatus_waist_error(msg_);
  }

private:
  ::genie_msgs::msg::WholeBodyStatus msg_;
};

class Init_WholeBodyStatus_right_end_error
{
public:
  explicit Init_WholeBodyStatus_right_end_error(::genie_msgs::msg::WholeBodyStatus & msg)
  : msg_(msg)
  {}
  Init_WholeBodyStatus_left_end_error right_end_error(::genie_msgs::msg::WholeBodyStatus::_right_end_error_type arg)
  {
    msg_.right_end_error = std::move(arg);
    return Init_WholeBodyStatus_left_end_error(msg_);
  }

private:
  ::genie_msgs::msg::WholeBodyStatus msg_;
};

class Init_WholeBodyStatus_left_arm_estop
{
public:
  explicit Init_WholeBodyStatus_left_arm_estop(::genie_msgs::msg::WholeBodyStatus & msg)
  : msg_(msg)
  {}
  Init_WholeBodyStatus_right_end_error left_arm_estop(::genie_msgs::msg::WholeBodyStatus::_left_arm_estop_type arg)
  {
    msg_.left_arm_estop = std::move(arg);
    return Init_WholeBodyStatus_right_end_error(msg_);
  }

private:
  ::genie_msgs::msg::WholeBodyStatus msg_;
};

class Init_WholeBodyStatus_right_arm_estop
{
public:
  explicit Init_WholeBodyStatus_right_arm_estop(::genie_msgs::msg::WholeBodyStatus & msg)
  : msg_(msg)
  {}
  Init_WholeBodyStatus_left_arm_estop right_arm_estop(::genie_msgs::msg::WholeBodyStatus::_right_arm_estop_type arg)
  {
    msg_.right_arm_estop = std::move(arg);
    return Init_WholeBodyStatus_left_arm_estop(msg_);
  }

private:
  ::genie_msgs::msg::WholeBodyStatus msg_;
};

class Init_WholeBodyStatus_left_arm_control
{
public:
  explicit Init_WholeBodyStatus_left_arm_control(::genie_msgs::msg::WholeBodyStatus & msg)
  : msg_(msg)
  {}
  Init_WholeBodyStatus_right_arm_estop left_arm_control(::genie_msgs::msg::WholeBodyStatus::_left_arm_control_type arg)
  {
    msg_.left_arm_control = std::move(arg);
    return Init_WholeBodyStatus_right_arm_estop(msg_);
  }

private:
  ::genie_msgs::msg::WholeBodyStatus msg_;
};

class Init_WholeBodyStatus_right_arm_control
{
public:
  explicit Init_WholeBodyStatus_right_arm_control(::genie_msgs::msg::WholeBodyStatus & msg)
  : msg_(msg)
  {}
  Init_WholeBodyStatus_left_arm_control right_arm_control(::genie_msgs::msg::WholeBodyStatus::_right_arm_control_type arg)
  {
    msg_.right_arm_control = std::move(arg);
    return Init_WholeBodyStatus_left_arm_control(msg_);
  }

private:
  ::genie_msgs::msg::WholeBodyStatus msg_;
};

class Init_WholeBodyStatus_left_arm_error
{
public:
  explicit Init_WholeBodyStatus_left_arm_error(::genie_msgs::msg::WholeBodyStatus & msg)
  : msg_(msg)
  {}
  Init_WholeBodyStatus_right_arm_control left_arm_error(::genie_msgs::msg::WholeBodyStatus::_left_arm_error_type arg)
  {
    msg_.left_arm_error = std::move(arg);
    return Init_WholeBodyStatus_right_arm_control(msg_);
  }

private:
  ::genie_msgs::msg::WholeBodyStatus msg_;
};

class Init_WholeBodyStatus_right_arm_error
{
public:
  explicit Init_WholeBodyStatus_right_arm_error(::genie_msgs::msg::WholeBodyStatus & msg)
  : msg_(msg)
  {}
  Init_WholeBodyStatus_left_arm_error right_arm_error(::genie_msgs::msg::WholeBodyStatus::_right_arm_error_type arg)
  {
    msg_.right_arm_error = std::move(arg);
    return Init_WholeBodyStatus_left_arm_error(msg_);
  }

private:
  ::genie_msgs::msg::WholeBodyStatus msg_;
};

class Init_WholeBodyStatus_header
{
public:
  Init_WholeBodyStatus_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_WholeBodyStatus_right_arm_error header(::genie_msgs::msg::WholeBodyStatus::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_WholeBodyStatus_right_arm_error(msg_);
  }

private:
  ::genie_msgs::msg::WholeBodyStatus msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::WholeBodyStatus>()
{
  return genie_msgs::msg::builder::Init_WholeBodyStatus_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__WHOLE_BODY_STATUS__BUILDER_HPP_
