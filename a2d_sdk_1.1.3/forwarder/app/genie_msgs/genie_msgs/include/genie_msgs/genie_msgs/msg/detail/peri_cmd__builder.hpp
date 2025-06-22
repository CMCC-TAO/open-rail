// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/PeriCmd.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__PERI_CMD__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__PERI_CMD__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/peri_cmd__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_PeriCmd_agv_power_ctrl_req
{
public:
  explicit Init_PeriCmd_agv_power_ctrl_req(::genie_msgs::msg::PeriCmd & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::PeriCmd agv_power_ctrl_req(::genie_msgs::msg::PeriCmd::_agv_power_ctrl_req_type arg)
  {
    msg_.agv_power_ctrl_req = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::PeriCmd msg_;
};

class Init_PeriCmd_head_pitch_motor_power_ctrl_req
{
public:
  explicit Init_PeriCmd_head_pitch_motor_power_ctrl_req(::genie_msgs::msg::PeriCmd & msg)
  : msg_(msg)
  {}
  Init_PeriCmd_agv_power_ctrl_req head_pitch_motor_power_ctrl_req(::genie_msgs::msg::PeriCmd::_head_pitch_motor_power_ctrl_req_type arg)
  {
    msg_.head_pitch_motor_power_ctrl_req = std::move(arg);
    return Init_PeriCmd_agv_power_ctrl_req(msg_);
  }

private:
  ::genie_msgs::msg::PeriCmd msg_;
};

class Init_PeriCmd_head_yaw_motor_power_ctrl_req
{
public:
  explicit Init_PeriCmd_head_yaw_motor_power_ctrl_req(::genie_msgs::msg::PeriCmd & msg)
  : msg_(msg)
  {}
  Init_PeriCmd_head_pitch_motor_power_ctrl_req head_yaw_motor_power_ctrl_req(::genie_msgs::msg::PeriCmd::_head_yaw_motor_power_ctrl_req_type arg)
  {
    msg_.head_yaw_motor_power_ctrl_req = std::move(arg);
    return Init_PeriCmd_head_pitch_motor_power_ctrl_req(msg_);
  }

private:
  ::genie_msgs::msg::PeriCmd msg_;
};

class Init_PeriCmd_lift_motor_power_ctrl_req
{
public:
  explicit Init_PeriCmd_lift_motor_power_ctrl_req(::genie_msgs::msg::PeriCmd & msg)
  : msg_(msg)
  {}
  Init_PeriCmd_head_yaw_motor_power_ctrl_req lift_motor_power_ctrl_req(::genie_msgs::msg::PeriCmd::_lift_motor_power_ctrl_req_type arg)
  {
    msg_.lift_motor_power_ctrl_req = std::move(arg);
    return Init_PeriCmd_head_yaw_motor_power_ctrl_req(msg_);
  }

private:
  ::genie_msgs::msg::PeriCmd msg_;
};

class Init_PeriCmd_waist_pitch_motor_power_ctrl_req
{
public:
  explicit Init_PeriCmd_waist_pitch_motor_power_ctrl_req(::genie_msgs::msg::PeriCmd & msg)
  : msg_(msg)
  {}
  Init_PeriCmd_lift_motor_power_ctrl_req waist_pitch_motor_power_ctrl_req(::genie_msgs::msg::PeriCmd::_waist_pitch_motor_power_ctrl_req_type arg)
  {
    msg_.waist_pitch_motor_power_ctrl_req = std::move(arg);
    return Init_PeriCmd_lift_motor_power_ctrl_req(msg_);
  }

private:
  ::genie_msgs::msg::PeriCmd msg_;
};

class Init_PeriCmd_right_end_power_ctrl_req
{
public:
  explicit Init_PeriCmd_right_end_power_ctrl_req(::genie_msgs::msg::PeriCmd & msg)
  : msg_(msg)
  {}
  Init_PeriCmd_waist_pitch_motor_power_ctrl_req right_end_power_ctrl_req(::genie_msgs::msg::PeriCmd::_right_end_power_ctrl_req_type arg)
  {
    msg_.right_end_power_ctrl_req = std::move(arg);
    return Init_PeriCmd_waist_pitch_motor_power_ctrl_req(msg_);
  }

private:
  ::genie_msgs::msg::PeriCmd msg_;
};

class Init_PeriCmd_left_end_power_ctrl_req
{
public:
  explicit Init_PeriCmd_left_end_power_ctrl_req(::genie_msgs::msg::PeriCmd & msg)
  : msg_(msg)
  {}
  Init_PeriCmd_right_end_power_ctrl_req left_end_power_ctrl_req(::genie_msgs::msg::PeriCmd::_left_end_power_ctrl_req_type arg)
  {
    msg_.left_end_power_ctrl_req = std::move(arg);
    return Init_PeriCmd_right_end_power_ctrl_req(msg_);
  }

private:
  ::genie_msgs::msg::PeriCmd msg_;
};

class Init_PeriCmd_right_arm_power_ctrl_req
{
public:
  explicit Init_PeriCmd_right_arm_power_ctrl_req(::genie_msgs::msg::PeriCmd & msg)
  : msg_(msg)
  {}
  Init_PeriCmd_left_end_power_ctrl_req right_arm_power_ctrl_req(::genie_msgs::msg::PeriCmd::_right_arm_power_ctrl_req_type arg)
  {
    msg_.right_arm_power_ctrl_req = std::move(arg);
    return Init_PeriCmd_left_end_power_ctrl_req(msg_);
  }

private:
  ::genie_msgs::msg::PeriCmd msg_;
};

class Init_PeriCmd_left_arm_power_ctrl_req
{
public:
  explicit Init_PeriCmd_left_arm_power_ctrl_req(::genie_msgs::msg::PeriCmd & msg)
  : msg_(msg)
  {}
  Init_PeriCmd_right_arm_power_ctrl_req left_arm_power_ctrl_req(::genie_msgs::msg::PeriCmd::_left_arm_power_ctrl_req_type arg)
  {
    msg_.left_arm_power_ctrl_req = std::move(arg);
    return Init_PeriCmd_right_arm_power_ctrl_req(msg_);
  }

private:
  ::genie_msgs::msg::PeriCmd msg_;
};

class Init_PeriCmd_feature_status
{
public:
  explicit Init_PeriCmd_feature_status(::genie_msgs::msg::PeriCmd & msg)
  : msg_(msg)
  {}
  Init_PeriCmd_left_arm_power_ctrl_req feature_status(::genie_msgs::msg::PeriCmd::_feature_status_type arg)
  {
    msg_.feature_status = std::move(arg);
    return Init_PeriCmd_left_arm_power_ctrl_req(msg_);
  }

private:
  ::genie_msgs::msg::PeriCmd msg_;
};

class Init_PeriCmd_work_mode
{
public:
  explicit Init_PeriCmd_work_mode(::genie_msgs::msg::PeriCmd & msg)
  : msg_(msg)
  {}
  Init_PeriCmd_feature_status work_mode(::genie_msgs::msg::PeriCmd::_work_mode_type arg)
  {
    msg_.work_mode = std::move(arg);
    return Init_PeriCmd_feature_status(msg_);
  }

private:
  ::genie_msgs::msg::PeriCmd msg_;
};

class Init_PeriCmd_agv_reset_request
{
public:
  explicit Init_PeriCmd_agv_reset_request(::genie_msgs::msg::PeriCmd & msg)
  : msg_(msg)
  {}
  Init_PeriCmd_work_mode agv_reset_request(::genie_msgs::msg::PeriCmd::_agv_reset_request_type arg)
  {
    msg_.agv_reset_request = std::move(arg);
    return Init_PeriCmd_work_mode(msg_);
  }

private:
  ::genie_msgs::msg::PeriCmd msg_;
};

class Init_PeriCmd_head_pitch_motor_reset_request
{
public:
  explicit Init_PeriCmd_head_pitch_motor_reset_request(::genie_msgs::msg::PeriCmd & msg)
  : msg_(msg)
  {}
  Init_PeriCmd_agv_reset_request head_pitch_motor_reset_request(::genie_msgs::msg::PeriCmd::_head_pitch_motor_reset_request_type arg)
  {
    msg_.head_pitch_motor_reset_request = std::move(arg);
    return Init_PeriCmd_agv_reset_request(msg_);
  }

private:
  ::genie_msgs::msg::PeriCmd msg_;
};

class Init_PeriCmd_head_yaw_motor_reset_request
{
public:
  explicit Init_PeriCmd_head_yaw_motor_reset_request(::genie_msgs::msg::PeriCmd & msg)
  : msg_(msg)
  {}
  Init_PeriCmd_head_pitch_motor_reset_request head_yaw_motor_reset_request(::genie_msgs::msg::PeriCmd::_head_yaw_motor_reset_request_type arg)
  {
    msg_.head_yaw_motor_reset_request = std::move(arg);
    return Init_PeriCmd_head_pitch_motor_reset_request(msg_);
  }

private:
  ::genie_msgs::msg::PeriCmd msg_;
};

class Init_PeriCmd_lift_motor_reset_request
{
public:
  explicit Init_PeriCmd_lift_motor_reset_request(::genie_msgs::msg::PeriCmd & msg)
  : msg_(msg)
  {}
  Init_PeriCmd_head_yaw_motor_reset_request lift_motor_reset_request(::genie_msgs::msg::PeriCmd::_lift_motor_reset_request_type arg)
  {
    msg_.lift_motor_reset_request = std::move(arg);
    return Init_PeriCmd_head_yaw_motor_reset_request(msg_);
  }

private:
  ::genie_msgs::msg::PeriCmd msg_;
};

class Init_PeriCmd_waist_pitch_motor_reset_request
{
public:
  explicit Init_PeriCmd_waist_pitch_motor_reset_request(::genie_msgs::msg::PeriCmd & msg)
  : msg_(msg)
  {}
  Init_PeriCmd_lift_motor_reset_request waist_pitch_motor_reset_request(::genie_msgs::msg::PeriCmd::_waist_pitch_motor_reset_request_type arg)
  {
    msg_.waist_pitch_motor_reset_request = std::move(arg);
    return Init_PeriCmd_lift_motor_reset_request(msg_);
  }

private:
  ::genie_msgs::msg::PeriCmd msg_;
};

class Init_PeriCmd_right_end_reset_request
{
public:
  explicit Init_PeriCmd_right_end_reset_request(::genie_msgs::msg::PeriCmd & msg)
  : msg_(msg)
  {}
  Init_PeriCmd_waist_pitch_motor_reset_request right_end_reset_request(::genie_msgs::msg::PeriCmd::_right_end_reset_request_type arg)
  {
    msg_.right_end_reset_request = std::move(arg);
    return Init_PeriCmd_waist_pitch_motor_reset_request(msg_);
  }

private:
  ::genie_msgs::msg::PeriCmd msg_;
};

class Init_PeriCmd_left_end_reset_request
{
public:
  explicit Init_PeriCmd_left_end_reset_request(::genie_msgs::msg::PeriCmd & msg)
  : msg_(msg)
  {}
  Init_PeriCmd_right_end_reset_request left_end_reset_request(::genie_msgs::msg::PeriCmd::_left_end_reset_request_type arg)
  {
    msg_.left_end_reset_request = std::move(arg);
    return Init_PeriCmd_right_end_reset_request(msg_);
  }

private:
  ::genie_msgs::msg::PeriCmd msg_;
};

class Init_PeriCmd_right_arm_reset_request
{
public:
  explicit Init_PeriCmd_right_arm_reset_request(::genie_msgs::msg::PeriCmd & msg)
  : msg_(msg)
  {}
  Init_PeriCmd_left_end_reset_request right_arm_reset_request(::genie_msgs::msg::PeriCmd::_right_arm_reset_request_type arg)
  {
    msg_.right_arm_reset_request = std::move(arg);
    return Init_PeriCmd_left_end_reset_request(msg_);
  }

private:
  ::genie_msgs::msg::PeriCmd msg_;
};

class Init_PeriCmd_left_arm_reset_request
{
public:
  explicit Init_PeriCmd_left_arm_reset_request(::genie_msgs::msg::PeriCmd & msg)
  : msg_(msg)
  {}
  Init_PeriCmd_right_arm_reset_request left_arm_reset_request(::genie_msgs::msg::PeriCmd::_left_arm_reset_request_type arg)
  {
    msg_.left_arm_reset_request = std::move(arg);
    return Init_PeriCmd_right_arm_reset_request(msg_);
  }

private:
  ::genie_msgs::msg::PeriCmd msg_;
};

class Init_PeriCmd_hub2_reset_request
{
public:
  explicit Init_PeriCmd_hub2_reset_request(::genie_msgs::msg::PeriCmd & msg)
  : msg_(msg)
  {}
  Init_PeriCmd_left_arm_reset_request hub2_reset_request(::genie_msgs::msg::PeriCmd::_hub2_reset_request_type arg)
  {
    msg_.hub2_reset_request = std::move(arg);
    return Init_PeriCmd_left_arm_reset_request(msg_);
  }

private:
  ::genie_msgs::msg::PeriCmd msg_;
};

class Init_PeriCmd_hub1_reset_request
{
public:
  explicit Init_PeriCmd_hub1_reset_request(::genie_msgs::msg::PeriCmd & msg)
  : msg_(msg)
  {}
  Init_PeriCmd_hub2_reset_request hub1_reset_request(::genie_msgs::msg::PeriCmd::_hub1_reset_request_type arg)
  {
    msg_.hub1_reset_request = std::move(arg);
    return Init_PeriCmd_hub2_reset_request(msg_);
  }

private:
  ::genie_msgs::msg::PeriCmd msg_;
};

class Init_PeriCmd_soft_emergency_stop
{
public:
  explicit Init_PeriCmd_soft_emergency_stop(::genie_msgs::msg::PeriCmd & msg)
  : msg_(msg)
  {}
  Init_PeriCmd_hub1_reset_request soft_emergency_stop(::genie_msgs::msg::PeriCmd::_soft_emergency_stop_type arg)
  {
    msg_.soft_emergency_stop = std::move(arg);
    return Init_PeriCmd_hub1_reset_request(msg_);
  }

private:
  ::genie_msgs::msg::PeriCmd msg_;
};

class Init_PeriCmd_compute_center_ready_shut_down
{
public:
  explicit Init_PeriCmd_compute_center_ready_shut_down(::genie_msgs::msg::PeriCmd & msg)
  : msg_(msg)
  {}
  Init_PeriCmd_soft_emergency_stop compute_center_ready_shut_down(::genie_msgs::msg::PeriCmd::_compute_center_ready_shut_down_type arg)
  {
    msg_.compute_center_ready_shut_down = std::move(arg);
    return Init_PeriCmd_soft_emergency_stop(msg_);
  }

private:
  ::genie_msgs::msg::PeriCmd msg_;
};

class Init_PeriCmd_header
{
public:
  Init_PeriCmd_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_PeriCmd_compute_center_ready_shut_down header(::genie_msgs::msg::PeriCmd::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_PeriCmd_compute_center_ready_shut_down(msg_);
  }

private:
  ::genie_msgs::msg::PeriCmd msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::PeriCmd>()
{
  return genie_msgs::msg::builder::Init_PeriCmd_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__PERI_CMD__BUILDER_HPP_
