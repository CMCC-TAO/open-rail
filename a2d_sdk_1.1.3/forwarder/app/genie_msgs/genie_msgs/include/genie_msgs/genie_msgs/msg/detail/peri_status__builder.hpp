// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/PeriStatus.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__PERI_STATUS__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__PERI_STATUS__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/peri_status__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_PeriStatus_power_board_serial_number
{
public:
  explicit Init_PeriStatus_power_board_serial_number(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::PeriStatus power_board_serial_number(::genie_msgs::msg::PeriStatus::_power_board_serial_number_type arg)
  {
    msg_.power_board_serial_number = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_power_board_hardware_version
{
public:
  explicit Init_PeriStatus_power_board_hardware_version(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_power_board_serial_number power_board_hardware_version(::genie_msgs::msg::PeriStatus::_power_board_hardware_version_type arg)
  {
    msg_.power_board_hardware_version = std::move(arg);
    return Init_PeriStatus_power_board_serial_number(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_power_board_software_version
{
public:
  explicit Init_PeriStatus_power_board_software_version(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_power_board_hardware_version power_board_software_version(::genie_msgs::msg::PeriStatus::_power_board_software_version_type arg)
  {
    msg_.power_board_software_version = std::move(arg);
    return Init_PeriStatus_power_board_hardware_version(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_emergency_stop_err_fedback
{
public:
  explicit Init_PeriStatus_emergency_stop_err_fedback(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_power_board_software_version emergency_stop_err_fedback(::genie_msgs::msg::PeriStatus::_emergency_stop_err_fedback_type arg)
  {
    msg_.emergency_stop_err_fedback = std::move(arg);
    return Init_PeriStatus_power_board_software_version(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_agv_voltage
{
public:
  explicit Init_PeriStatus_agv_voltage(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_emergency_stop_err_fedback agv_voltage(::genie_msgs::msg::PeriStatus::_agv_voltage_type arg)
  {
    msg_.agv_voltage = std::move(arg);
    return Init_PeriStatus_emergency_stop_err_fedback(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_head_pitch_motor_voltage
{
public:
  explicit Init_PeriStatus_head_pitch_motor_voltage(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_agv_voltage head_pitch_motor_voltage(::genie_msgs::msg::PeriStatus::_head_pitch_motor_voltage_type arg)
  {
    msg_.head_pitch_motor_voltage = std::move(arg);
    return Init_PeriStatus_agv_voltage(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_head_yaw_motor_voltage
{
public:
  explicit Init_PeriStatus_head_yaw_motor_voltage(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_head_pitch_motor_voltage head_yaw_motor_voltage(::genie_msgs::msg::PeriStatus::_head_yaw_motor_voltage_type arg)
  {
    msg_.head_yaw_motor_voltage = std::move(arg);
    return Init_PeriStatus_head_pitch_motor_voltage(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_lift_motor_voltage
{
public:
  explicit Init_PeriStatus_lift_motor_voltage(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_head_yaw_motor_voltage lift_motor_voltage(::genie_msgs::msg::PeriStatus::_lift_motor_voltage_type arg)
  {
    msg_.lift_motor_voltage = std::move(arg);
    return Init_PeriStatus_head_yaw_motor_voltage(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_waist_pitch_motor_voltage
{
public:
  explicit Init_PeriStatus_waist_pitch_motor_voltage(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_lift_motor_voltage waist_pitch_motor_voltage(::genie_msgs::msg::PeriStatus::_waist_pitch_motor_voltage_type arg)
  {
    msg_.waist_pitch_motor_voltage = std::move(arg);
    return Init_PeriStatus_lift_motor_voltage(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_right_end_voltage
{
public:
  explicit Init_PeriStatus_right_end_voltage(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_waist_pitch_motor_voltage right_end_voltage(::genie_msgs::msg::PeriStatus::_right_end_voltage_type arg)
  {
    msg_.right_end_voltage = std::move(arg);
    return Init_PeriStatus_waist_pitch_motor_voltage(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_left_end_voltage
{
public:
  explicit Init_PeriStatus_left_end_voltage(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_right_end_voltage left_end_voltage(::genie_msgs::msg::PeriStatus::_left_end_voltage_type arg)
  {
    msg_.left_end_voltage = std::move(arg);
    return Init_PeriStatus_right_end_voltage(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_agv_current
{
public:
  explicit Init_PeriStatus_agv_current(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_left_end_voltage agv_current(::genie_msgs::msg::PeriStatus::_agv_current_type arg)
  {
    msg_.agv_current = std::move(arg);
    return Init_PeriStatus_left_end_voltage(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_head_pitch_motor_current
{
public:
  explicit Init_PeriStatus_head_pitch_motor_current(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_agv_current head_pitch_motor_current(::genie_msgs::msg::PeriStatus::_head_pitch_motor_current_type arg)
  {
    msg_.head_pitch_motor_current = std::move(arg);
    return Init_PeriStatus_agv_current(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_head_yaw_motor_current
{
public:
  explicit Init_PeriStatus_head_yaw_motor_current(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_head_pitch_motor_current head_yaw_motor_current(::genie_msgs::msg::PeriStatus::_head_yaw_motor_current_type arg)
  {
    msg_.head_yaw_motor_current = std::move(arg);
    return Init_PeriStatus_head_pitch_motor_current(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_lift_motor_current
{
public:
  explicit Init_PeriStatus_lift_motor_current(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_head_yaw_motor_current lift_motor_current(::genie_msgs::msg::PeriStatus::_lift_motor_current_type arg)
  {
    msg_.lift_motor_current = std::move(arg);
    return Init_PeriStatus_head_yaw_motor_current(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_waist_pitch_motor_current
{
public:
  explicit Init_PeriStatus_waist_pitch_motor_current(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_lift_motor_current waist_pitch_motor_current(::genie_msgs::msg::PeriStatus::_waist_pitch_motor_current_type arg)
  {
    msg_.waist_pitch_motor_current = std::move(arg);
    return Init_PeriStatus_lift_motor_current(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_right_end_current
{
public:
  explicit Init_PeriStatus_right_end_current(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_waist_pitch_motor_current right_end_current(::genie_msgs::msg::PeriStatus::_right_end_current_type arg)
  {
    msg_.right_end_current = std::move(arg);
    return Init_PeriStatus_waist_pitch_motor_current(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_left_end_current
{
public:
  explicit Init_PeriStatus_left_end_current(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_right_end_current left_end_current(::genie_msgs::msg::PeriStatus::_left_end_current_type arg)
  {
    msg_.left_end_current = std::move(arg);
    return Init_PeriStatus_right_end_current(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_power_ctrl_req_failreason
{
public:
  explicit Init_PeriStatus_power_ctrl_req_failreason(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_left_end_current power_ctrl_req_failreason(::genie_msgs::msg::PeriStatus::_power_ctrl_req_failreason_type arg)
  {
    msg_.power_ctrl_req_failreason = std::move(arg);
    return Init_PeriStatus_left_end_current(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_agv_power_ctrl_req_feedback
{
public:
  explicit Init_PeriStatus_agv_power_ctrl_req_feedback(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_power_ctrl_req_failreason agv_power_ctrl_req_feedback(::genie_msgs::msg::PeriStatus::_agv_power_ctrl_req_feedback_type arg)
  {
    msg_.agv_power_ctrl_req_feedback = std::move(arg);
    return Init_PeriStatus_power_ctrl_req_failreason(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_head_pitch_motor_power_ctrl_req_feedback
{
public:
  explicit Init_PeriStatus_head_pitch_motor_power_ctrl_req_feedback(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_agv_power_ctrl_req_feedback head_pitch_motor_power_ctrl_req_feedback(::genie_msgs::msg::PeriStatus::_head_pitch_motor_power_ctrl_req_feedback_type arg)
  {
    msg_.head_pitch_motor_power_ctrl_req_feedback = std::move(arg);
    return Init_PeriStatus_agv_power_ctrl_req_feedback(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_head_yaw_motor_power_ctrl_req_feedback
{
public:
  explicit Init_PeriStatus_head_yaw_motor_power_ctrl_req_feedback(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_head_pitch_motor_power_ctrl_req_feedback head_yaw_motor_power_ctrl_req_feedback(::genie_msgs::msg::PeriStatus::_head_yaw_motor_power_ctrl_req_feedback_type arg)
  {
    msg_.head_yaw_motor_power_ctrl_req_feedback = std::move(arg);
    return Init_PeriStatus_head_pitch_motor_power_ctrl_req_feedback(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_lift_motor_power_ctrl_req_feedback
{
public:
  explicit Init_PeriStatus_lift_motor_power_ctrl_req_feedback(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_head_yaw_motor_power_ctrl_req_feedback lift_motor_power_ctrl_req_feedback(::genie_msgs::msg::PeriStatus::_lift_motor_power_ctrl_req_feedback_type arg)
  {
    msg_.lift_motor_power_ctrl_req_feedback = std::move(arg);
    return Init_PeriStatus_head_yaw_motor_power_ctrl_req_feedback(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_waist_pitch_motor_power_ctrl_req_feedback
{
public:
  explicit Init_PeriStatus_waist_pitch_motor_power_ctrl_req_feedback(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_lift_motor_power_ctrl_req_feedback waist_pitch_motor_power_ctrl_req_feedback(::genie_msgs::msg::PeriStatus::_waist_pitch_motor_power_ctrl_req_feedback_type arg)
  {
    msg_.waist_pitch_motor_power_ctrl_req_feedback = std::move(arg);
    return Init_PeriStatus_lift_motor_power_ctrl_req_feedback(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_right_end_power_ctrl_req_feedback
{
public:
  explicit Init_PeriStatus_right_end_power_ctrl_req_feedback(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_waist_pitch_motor_power_ctrl_req_feedback right_end_power_ctrl_req_feedback(::genie_msgs::msg::PeriStatus::_right_end_power_ctrl_req_feedback_type arg)
  {
    msg_.right_end_power_ctrl_req_feedback = std::move(arg);
    return Init_PeriStatus_waist_pitch_motor_power_ctrl_req_feedback(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_left_end_power_ctrl_req_feedback
{
public:
  explicit Init_PeriStatus_left_end_power_ctrl_req_feedback(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_right_end_power_ctrl_req_feedback left_end_power_ctrl_req_feedback(::genie_msgs::msg::PeriStatus::_left_end_power_ctrl_req_feedback_type arg)
  {
    msg_.left_end_power_ctrl_req_feedback = std::move(arg);
    return Init_PeriStatus_right_end_power_ctrl_req_feedback(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_right_arm_power_ctrl_req_feedback
{
public:
  explicit Init_PeriStatus_right_arm_power_ctrl_req_feedback(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_left_end_power_ctrl_req_feedback right_arm_power_ctrl_req_feedback(::genie_msgs::msg::PeriStatus::_right_arm_power_ctrl_req_feedback_type arg)
  {
    msg_.right_arm_power_ctrl_req_feedback = std::move(arg);
    return Init_PeriStatus_left_end_power_ctrl_req_feedback(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_left_arm_power_ctrl_req_feedback
{
public:
  explicit Init_PeriStatus_left_arm_power_ctrl_req_feedback(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_right_arm_power_ctrl_req_feedback left_arm_power_ctrl_req_feedback(::genie_msgs::msg::PeriStatus::_left_arm_power_ctrl_req_feedback_type arg)
  {
    msg_.left_arm_power_ctrl_req_feedback = std::move(arg);
    return Init_PeriStatus_right_arm_power_ctrl_req_feedback(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_feature_status
{
public:
  explicit Init_PeriStatus_feature_status(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_left_arm_power_ctrl_req_feedback feature_status(::genie_msgs::msg::PeriStatus::_feature_status_type arg)
  {
    msg_.feature_status = std::move(arg);
    return Init_PeriStatus_left_arm_power_ctrl_req_feedback(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_power_pcb_work_mode
{
public:
  explicit Init_PeriStatus_power_pcb_work_mode(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_feature_status power_pcb_work_mode(::genie_msgs::msg::PeriStatus::_power_pcb_work_mode_type arg)
  {
    msg_.power_pcb_work_mode = std::move(arg);
    return Init_PeriStatus_feature_status(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_agv_reset_request_feedback
{
public:
  explicit Init_PeriStatus_agv_reset_request_feedback(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_power_pcb_work_mode agv_reset_request_feedback(::genie_msgs::msg::PeriStatus::_agv_reset_request_feedback_type arg)
  {
    msg_.agv_reset_request_feedback = std::move(arg);
    return Init_PeriStatus_power_pcb_work_mode(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_head_pitch_motor_reset_request_feedback
{
public:
  explicit Init_PeriStatus_head_pitch_motor_reset_request_feedback(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_agv_reset_request_feedback head_pitch_motor_reset_request_feedback(::genie_msgs::msg::PeriStatus::_head_pitch_motor_reset_request_feedback_type arg)
  {
    msg_.head_pitch_motor_reset_request_feedback = std::move(arg);
    return Init_PeriStatus_agv_reset_request_feedback(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_head_yaw_motor_reset_request_feedback
{
public:
  explicit Init_PeriStatus_head_yaw_motor_reset_request_feedback(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_head_pitch_motor_reset_request_feedback head_yaw_motor_reset_request_feedback(::genie_msgs::msg::PeriStatus::_head_yaw_motor_reset_request_feedback_type arg)
  {
    msg_.head_yaw_motor_reset_request_feedback = std::move(arg);
    return Init_PeriStatus_head_pitch_motor_reset_request_feedback(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_lift_motor_reset_request_feedback
{
public:
  explicit Init_PeriStatus_lift_motor_reset_request_feedback(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_head_yaw_motor_reset_request_feedback lift_motor_reset_request_feedback(::genie_msgs::msg::PeriStatus::_lift_motor_reset_request_feedback_type arg)
  {
    msg_.lift_motor_reset_request_feedback = std::move(arg);
    return Init_PeriStatus_head_yaw_motor_reset_request_feedback(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_waist_pitch_motor_reset_request_feedback
{
public:
  explicit Init_PeriStatus_waist_pitch_motor_reset_request_feedback(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_lift_motor_reset_request_feedback waist_pitch_motor_reset_request_feedback(::genie_msgs::msg::PeriStatus::_waist_pitch_motor_reset_request_feedback_type arg)
  {
    msg_.waist_pitch_motor_reset_request_feedback = std::move(arg);
    return Init_PeriStatus_lift_motor_reset_request_feedback(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_right_end_reset_request_feedback
{
public:
  explicit Init_PeriStatus_right_end_reset_request_feedback(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_waist_pitch_motor_reset_request_feedback right_end_reset_request_feedback(::genie_msgs::msg::PeriStatus::_right_end_reset_request_feedback_type arg)
  {
    msg_.right_end_reset_request_feedback = std::move(arg);
    return Init_PeriStatus_waist_pitch_motor_reset_request_feedback(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_left_end_reset_request_feedback
{
public:
  explicit Init_PeriStatus_left_end_reset_request_feedback(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_right_end_reset_request_feedback left_end_reset_request_feedback(::genie_msgs::msg::PeriStatus::_left_end_reset_request_feedback_type arg)
  {
    msg_.left_end_reset_request_feedback = std::move(arg);
    return Init_PeriStatus_right_end_reset_request_feedback(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_right_arm_reset_request_feedback
{
public:
  explicit Init_PeriStatus_right_arm_reset_request_feedback(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_left_end_reset_request_feedback right_arm_reset_request_feedback(::genie_msgs::msg::PeriStatus::_right_arm_reset_request_feedback_type arg)
  {
    msg_.right_arm_reset_request_feedback = std::move(arg);
    return Init_PeriStatus_left_end_reset_request_feedback(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_left_arm_reset_request_feedback
{
public:
  explicit Init_PeriStatus_left_arm_reset_request_feedback(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_right_arm_reset_request_feedback left_arm_reset_request_feedback(::genie_msgs::msg::PeriStatus::_left_arm_reset_request_feedback_type arg)
  {
    msg_.left_arm_reset_request_feedback = std::move(arg);
    return Init_PeriStatus_right_arm_reset_request_feedback(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_hub2_reset_request_feedback
{
public:
  explicit Init_PeriStatus_hub2_reset_request_feedback(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_left_arm_reset_request_feedback hub2_reset_request_feedback(::genie_msgs::msg::PeriStatus::_hub2_reset_request_feedback_type arg)
  {
    msg_.hub2_reset_request_feedback = std::move(arg);
    return Init_PeriStatus_left_arm_reset_request_feedback(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_hub1_reset_request_feedback
{
public:
  explicit Init_PeriStatus_hub1_reset_request_feedback(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_hub2_reset_request_feedback hub1_reset_request_feedback(::genie_msgs::msg::PeriStatus::_hub1_reset_request_feedback_type arg)
  {
    msg_.hub1_reset_request_feedback = std::move(arg);
    return Init_PeriStatus_hub2_reset_request_feedback(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_button_emergency_stop
{
public:
  explicit Init_PeriStatus_button_emergency_stop(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_hub1_reset_request_feedback button_emergency_stop(::genie_msgs::msg::PeriStatus::_button_emergency_stop_type arg)
  {
    msg_.button_emergency_stop = std::move(arg);
    return Init_PeriStatus_hub1_reset_request_feedback(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_pedal_emergency_stop
{
public:
  explicit Init_PeriStatus_pedal_emergency_stop(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_button_emergency_stop pedal_emergency_stop(::genie_msgs::msg::PeriStatus::_pedal_emergency_stop_type arg)
  {
    msg_.pedal_emergency_stop = std::move(arg);
    return Init_PeriStatus_button_emergency_stop(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_soft_emergency_stop_feedback
{
public:
  explicit Init_PeriStatus_soft_emergency_stop_feedback(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_pedal_emergency_stop soft_emergency_stop_feedback(::genie_msgs::msg::PeriStatus::_soft_emergency_stop_feedback_type arg)
  {
    msg_.soft_emergency_stop_feedback = std::move(arg);
    return Init_PeriStatus_pedal_emergency_stop(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_shut_down_compute_center_request
{
public:
  explicit Init_PeriStatus_shut_down_compute_center_request(::genie_msgs::msg::PeriStatus & msg)
  : msg_(msg)
  {}
  Init_PeriStatus_soft_emergency_stop_feedback shut_down_compute_center_request(::genie_msgs::msg::PeriStatus::_shut_down_compute_center_request_type arg)
  {
    msg_.shut_down_compute_center_request = std::move(arg);
    return Init_PeriStatus_soft_emergency_stop_feedback(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

class Init_PeriStatus_header
{
public:
  Init_PeriStatus_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_PeriStatus_shut_down_compute_center_request header(::genie_msgs::msg::PeriStatus::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_PeriStatus_shut_down_compute_center_request(msg_);
  }

private:
  ::genie_msgs::msg::PeriStatus msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::PeriStatus>()
{
  return genie_msgs::msg::builder::Init_PeriStatus_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__PERI_STATUS__BUILDER_HPP_
