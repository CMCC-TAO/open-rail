// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from genie_msgs:msg/PeriStatus.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__PERI_STATUS__TRAITS_HPP_
#define GENIE_MSGS__MSG__DETAIL__PERI_STATUS__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "genie_msgs/msg/detail/peri_status__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"

namespace genie_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const PeriStatus & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: shut_down_compute_center_request
  {
    out << "shut_down_compute_center_request: ";
    rosidl_generator_traits::value_to_yaml(msg.shut_down_compute_center_request, out);
    out << ", ";
  }

  // member: soft_emergency_stop_feedback
  {
    out << "soft_emergency_stop_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.soft_emergency_stop_feedback, out);
    out << ", ";
  }

  // member: pedal_emergency_stop
  {
    out << "pedal_emergency_stop: ";
    rosidl_generator_traits::value_to_yaml(msg.pedal_emergency_stop, out);
    out << ", ";
  }

  // member: button_emergency_stop
  {
    out << "button_emergency_stop: ";
    rosidl_generator_traits::value_to_yaml(msg.button_emergency_stop, out);
    out << ", ";
  }

  // member: hub1_reset_request_feedback
  {
    out << "hub1_reset_request_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.hub1_reset_request_feedback, out);
    out << ", ";
  }

  // member: hub2_reset_request_feedback
  {
    out << "hub2_reset_request_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.hub2_reset_request_feedback, out);
    out << ", ";
  }

  // member: left_arm_reset_request_feedback
  {
    out << "left_arm_reset_request_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.left_arm_reset_request_feedback, out);
    out << ", ";
  }

  // member: right_arm_reset_request_feedback
  {
    out << "right_arm_reset_request_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.right_arm_reset_request_feedback, out);
    out << ", ";
  }

  // member: left_end_reset_request_feedback
  {
    out << "left_end_reset_request_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.left_end_reset_request_feedback, out);
    out << ", ";
  }

  // member: right_end_reset_request_feedback
  {
    out << "right_end_reset_request_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.right_end_reset_request_feedback, out);
    out << ", ";
  }

  // member: waist_pitch_motor_reset_request_feedback
  {
    out << "waist_pitch_motor_reset_request_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.waist_pitch_motor_reset_request_feedback, out);
    out << ", ";
  }

  // member: lift_motor_reset_request_feedback
  {
    out << "lift_motor_reset_request_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.lift_motor_reset_request_feedback, out);
    out << ", ";
  }

  // member: head_yaw_motor_reset_request_feedback
  {
    out << "head_yaw_motor_reset_request_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.head_yaw_motor_reset_request_feedback, out);
    out << ", ";
  }

  // member: head_pitch_motor_reset_request_feedback
  {
    out << "head_pitch_motor_reset_request_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.head_pitch_motor_reset_request_feedback, out);
    out << ", ";
  }

  // member: agv_reset_request_feedback
  {
    out << "agv_reset_request_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.agv_reset_request_feedback, out);
    out << ", ";
  }

  // member: power_pcb_work_mode
  {
    out << "power_pcb_work_mode: ";
    rosidl_generator_traits::value_to_yaml(msg.power_pcb_work_mode, out);
    out << ", ";
  }

  // member: feature_status
  {
    out << "feature_status: ";
    rosidl_generator_traits::value_to_yaml(msg.feature_status, out);
    out << ", ";
  }

  // member: left_arm_power_ctrl_req_feedback
  {
    out << "left_arm_power_ctrl_req_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.left_arm_power_ctrl_req_feedback, out);
    out << ", ";
  }

  // member: right_arm_power_ctrl_req_feedback
  {
    out << "right_arm_power_ctrl_req_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.right_arm_power_ctrl_req_feedback, out);
    out << ", ";
  }

  // member: left_end_power_ctrl_req_feedback
  {
    out << "left_end_power_ctrl_req_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.left_end_power_ctrl_req_feedback, out);
    out << ", ";
  }

  // member: right_end_power_ctrl_req_feedback
  {
    out << "right_end_power_ctrl_req_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.right_end_power_ctrl_req_feedback, out);
    out << ", ";
  }

  // member: waist_pitch_motor_power_ctrl_req_feedback
  {
    out << "waist_pitch_motor_power_ctrl_req_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.waist_pitch_motor_power_ctrl_req_feedback, out);
    out << ", ";
  }

  // member: lift_motor_power_ctrl_req_feedback
  {
    out << "lift_motor_power_ctrl_req_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.lift_motor_power_ctrl_req_feedback, out);
    out << ", ";
  }

  // member: head_yaw_motor_power_ctrl_req_feedback
  {
    out << "head_yaw_motor_power_ctrl_req_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.head_yaw_motor_power_ctrl_req_feedback, out);
    out << ", ";
  }

  // member: head_pitch_motor_power_ctrl_req_feedback
  {
    out << "head_pitch_motor_power_ctrl_req_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.head_pitch_motor_power_ctrl_req_feedback, out);
    out << ", ";
  }

  // member: agv_power_ctrl_req_feedback
  {
    out << "agv_power_ctrl_req_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.agv_power_ctrl_req_feedback, out);
    out << ", ";
  }

  // member: power_ctrl_req_failreason
  {
    out << "power_ctrl_req_failreason: ";
    rosidl_generator_traits::value_to_yaml(msg.power_ctrl_req_failreason, out);
    out << ", ";
  }

  // member: left_end_current
  {
    out << "left_end_current: ";
    rosidl_generator_traits::value_to_yaml(msg.left_end_current, out);
    out << ", ";
  }

  // member: right_end_current
  {
    out << "right_end_current: ";
    rosidl_generator_traits::value_to_yaml(msg.right_end_current, out);
    out << ", ";
  }

  // member: waist_pitch_motor_current
  {
    out << "waist_pitch_motor_current: ";
    rosidl_generator_traits::value_to_yaml(msg.waist_pitch_motor_current, out);
    out << ", ";
  }

  // member: lift_motor_current
  {
    out << "lift_motor_current: ";
    rosidl_generator_traits::value_to_yaml(msg.lift_motor_current, out);
    out << ", ";
  }

  // member: head_yaw_motor_current
  {
    out << "head_yaw_motor_current: ";
    rosidl_generator_traits::value_to_yaml(msg.head_yaw_motor_current, out);
    out << ", ";
  }

  // member: head_pitch_motor_current
  {
    out << "head_pitch_motor_current: ";
    rosidl_generator_traits::value_to_yaml(msg.head_pitch_motor_current, out);
    out << ", ";
  }

  // member: agv_current
  {
    out << "agv_current: ";
    rosidl_generator_traits::value_to_yaml(msg.agv_current, out);
    out << ", ";
  }

  // member: left_end_voltage
  {
    out << "left_end_voltage: ";
    rosidl_generator_traits::value_to_yaml(msg.left_end_voltage, out);
    out << ", ";
  }

  // member: right_end_voltage
  {
    out << "right_end_voltage: ";
    rosidl_generator_traits::value_to_yaml(msg.right_end_voltage, out);
    out << ", ";
  }

  // member: waist_pitch_motor_voltage
  {
    out << "waist_pitch_motor_voltage: ";
    rosidl_generator_traits::value_to_yaml(msg.waist_pitch_motor_voltage, out);
    out << ", ";
  }

  // member: lift_motor_voltage
  {
    out << "lift_motor_voltage: ";
    rosidl_generator_traits::value_to_yaml(msg.lift_motor_voltage, out);
    out << ", ";
  }

  // member: head_yaw_motor_voltage
  {
    out << "head_yaw_motor_voltage: ";
    rosidl_generator_traits::value_to_yaml(msg.head_yaw_motor_voltage, out);
    out << ", ";
  }

  // member: head_pitch_motor_voltage
  {
    out << "head_pitch_motor_voltage: ";
    rosidl_generator_traits::value_to_yaml(msg.head_pitch_motor_voltage, out);
    out << ", ";
  }

  // member: agv_voltage
  {
    out << "agv_voltage: ";
    rosidl_generator_traits::value_to_yaml(msg.agv_voltage, out);
    out << ", ";
  }

  // member: emergency_stop_err_fedback
  {
    out << "emergency_stop_err_fedback: ";
    rosidl_generator_traits::value_to_yaml(msg.emergency_stop_err_fedback, out);
    out << ", ";
  }

  // member: power_board_software_version
  {
    out << "power_board_software_version: ";
    rosidl_generator_traits::value_to_yaml(msg.power_board_software_version, out);
    out << ", ";
  }

  // member: power_board_hardware_version
  {
    out << "power_board_hardware_version: ";
    rosidl_generator_traits::value_to_yaml(msg.power_board_hardware_version, out);
    out << ", ";
  }

  // member: power_board_serial_number
  {
    out << "power_board_serial_number: ";
    rosidl_generator_traits::value_to_yaml(msg.power_board_serial_number, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const PeriStatus & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: header
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "header:\n";
    to_block_style_yaml(msg.header, out, indentation + 2);
  }

  // member: shut_down_compute_center_request
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "shut_down_compute_center_request: ";
    rosidl_generator_traits::value_to_yaml(msg.shut_down_compute_center_request, out);
    out << "\n";
  }

  // member: soft_emergency_stop_feedback
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "soft_emergency_stop_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.soft_emergency_stop_feedback, out);
    out << "\n";
  }

  // member: pedal_emergency_stop
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "pedal_emergency_stop: ";
    rosidl_generator_traits::value_to_yaml(msg.pedal_emergency_stop, out);
    out << "\n";
  }

  // member: button_emergency_stop
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "button_emergency_stop: ";
    rosidl_generator_traits::value_to_yaml(msg.button_emergency_stop, out);
    out << "\n";
  }

  // member: hub1_reset_request_feedback
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "hub1_reset_request_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.hub1_reset_request_feedback, out);
    out << "\n";
  }

  // member: hub2_reset_request_feedback
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "hub2_reset_request_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.hub2_reset_request_feedback, out);
    out << "\n";
  }

  // member: left_arm_reset_request_feedback
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "left_arm_reset_request_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.left_arm_reset_request_feedback, out);
    out << "\n";
  }

  // member: right_arm_reset_request_feedback
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "right_arm_reset_request_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.right_arm_reset_request_feedback, out);
    out << "\n";
  }

  // member: left_end_reset_request_feedback
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "left_end_reset_request_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.left_end_reset_request_feedback, out);
    out << "\n";
  }

  // member: right_end_reset_request_feedback
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "right_end_reset_request_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.right_end_reset_request_feedback, out);
    out << "\n";
  }

  // member: waist_pitch_motor_reset_request_feedback
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "waist_pitch_motor_reset_request_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.waist_pitch_motor_reset_request_feedback, out);
    out << "\n";
  }

  // member: lift_motor_reset_request_feedback
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "lift_motor_reset_request_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.lift_motor_reset_request_feedback, out);
    out << "\n";
  }

  // member: head_yaw_motor_reset_request_feedback
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "head_yaw_motor_reset_request_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.head_yaw_motor_reset_request_feedback, out);
    out << "\n";
  }

  // member: head_pitch_motor_reset_request_feedback
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "head_pitch_motor_reset_request_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.head_pitch_motor_reset_request_feedback, out);
    out << "\n";
  }

  // member: agv_reset_request_feedback
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "agv_reset_request_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.agv_reset_request_feedback, out);
    out << "\n";
  }

  // member: power_pcb_work_mode
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "power_pcb_work_mode: ";
    rosidl_generator_traits::value_to_yaml(msg.power_pcb_work_mode, out);
    out << "\n";
  }

  // member: feature_status
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "feature_status: ";
    rosidl_generator_traits::value_to_yaml(msg.feature_status, out);
    out << "\n";
  }

  // member: left_arm_power_ctrl_req_feedback
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "left_arm_power_ctrl_req_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.left_arm_power_ctrl_req_feedback, out);
    out << "\n";
  }

  // member: right_arm_power_ctrl_req_feedback
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "right_arm_power_ctrl_req_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.right_arm_power_ctrl_req_feedback, out);
    out << "\n";
  }

  // member: left_end_power_ctrl_req_feedback
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "left_end_power_ctrl_req_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.left_end_power_ctrl_req_feedback, out);
    out << "\n";
  }

  // member: right_end_power_ctrl_req_feedback
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "right_end_power_ctrl_req_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.right_end_power_ctrl_req_feedback, out);
    out << "\n";
  }

  // member: waist_pitch_motor_power_ctrl_req_feedback
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "waist_pitch_motor_power_ctrl_req_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.waist_pitch_motor_power_ctrl_req_feedback, out);
    out << "\n";
  }

  // member: lift_motor_power_ctrl_req_feedback
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "lift_motor_power_ctrl_req_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.lift_motor_power_ctrl_req_feedback, out);
    out << "\n";
  }

  // member: head_yaw_motor_power_ctrl_req_feedback
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "head_yaw_motor_power_ctrl_req_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.head_yaw_motor_power_ctrl_req_feedback, out);
    out << "\n";
  }

  // member: head_pitch_motor_power_ctrl_req_feedback
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "head_pitch_motor_power_ctrl_req_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.head_pitch_motor_power_ctrl_req_feedback, out);
    out << "\n";
  }

  // member: agv_power_ctrl_req_feedback
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "agv_power_ctrl_req_feedback: ";
    rosidl_generator_traits::value_to_yaml(msg.agv_power_ctrl_req_feedback, out);
    out << "\n";
  }

  // member: power_ctrl_req_failreason
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "power_ctrl_req_failreason: ";
    rosidl_generator_traits::value_to_yaml(msg.power_ctrl_req_failreason, out);
    out << "\n";
  }

  // member: left_end_current
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "left_end_current: ";
    rosidl_generator_traits::value_to_yaml(msg.left_end_current, out);
    out << "\n";
  }

  // member: right_end_current
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "right_end_current: ";
    rosidl_generator_traits::value_to_yaml(msg.right_end_current, out);
    out << "\n";
  }

  // member: waist_pitch_motor_current
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "waist_pitch_motor_current: ";
    rosidl_generator_traits::value_to_yaml(msg.waist_pitch_motor_current, out);
    out << "\n";
  }

  // member: lift_motor_current
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "lift_motor_current: ";
    rosidl_generator_traits::value_to_yaml(msg.lift_motor_current, out);
    out << "\n";
  }

  // member: head_yaw_motor_current
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "head_yaw_motor_current: ";
    rosidl_generator_traits::value_to_yaml(msg.head_yaw_motor_current, out);
    out << "\n";
  }

  // member: head_pitch_motor_current
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "head_pitch_motor_current: ";
    rosidl_generator_traits::value_to_yaml(msg.head_pitch_motor_current, out);
    out << "\n";
  }

  // member: agv_current
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "agv_current: ";
    rosidl_generator_traits::value_to_yaml(msg.agv_current, out);
    out << "\n";
  }

  // member: left_end_voltage
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "left_end_voltage: ";
    rosidl_generator_traits::value_to_yaml(msg.left_end_voltage, out);
    out << "\n";
  }

  // member: right_end_voltage
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "right_end_voltage: ";
    rosidl_generator_traits::value_to_yaml(msg.right_end_voltage, out);
    out << "\n";
  }

  // member: waist_pitch_motor_voltage
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "waist_pitch_motor_voltage: ";
    rosidl_generator_traits::value_to_yaml(msg.waist_pitch_motor_voltage, out);
    out << "\n";
  }

  // member: lift_motor_voltage
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "lift_motor_voltage: ";
    rosidl_generator_traits::value_to_yaml(msg.lift_motor_voltage, out);
    out << "\n";
  }

  // member: head_yaw_motor_voltage
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "head_yaw_motor_voltage: ";
    rosidl_generator_traits::value_to_yaml(msg.head_yaw_motor_voltage, out);
    out << "\n";
  }

  // member: head_pitch_motor_voltage
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "head_pitch_motor_voltage: ";
    rosidl_generator_traits::value_to_yaml(msg.head_pitch_motor_voltage, out);
    out << "\n";
  }

  // member: agv_voltage
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "agv_voltage: ";
    rosidl_generator_traits::value_to_yaml(msg.agv_voltage, out);
    out << "\n";
  }

  // member: emergency_stop_err_fedback
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "emergency_stop_err_fedback: ";
    rosidl_generator_traits::value_to_yaml(msg.emergency_stop_err_fedback, out);
    out << "\n";
  }

  // member: power_board_software_version
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "power_board_software_version: ";
    rosidl_generator_traits::value_to_yaml(msg.power_board_software_version, out);
    out << "\n";
  }

  // member: power_board_hardware_version
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "power_board_hardware_version: ";
    rosidl_generator_traits::value_to_yaml(msg.power_board_hardware_version, out);
    out << "\n";
  }

  // member: power_board_serial_number
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "power_board_serial_number: ";
    rosidl_generator_traits::value_to_yaml(msg.power_board_serial_number, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const PeriStatus & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace msg

}  // namespace genie_msgs

namespace rosidl_generator_traits
{

[[deprecated("use genie_msgs::msg::to_block_style_yaml() instead")]]
inline void to_yaml(
  const genie_msgs::msg::PeriStatus & msg,
  std::ostream & out, size_t indentation = 0)
{
  genie_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use genie_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const genie_msgs::msg::PeriStatus & msg)
{
  return genie_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<genie_msgs::msg::PeriStatus>()
{
  return "genie_msgs::msg::PeriStatus";
}

template<>
inline const char * name<genie_msgs::msg::PeriStatus>()
{
  return "genie_msgs/msg/PeriStatus";
}

template<>
struct has_fixed_size<genie_msgs::msg::PeriStatus>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<genie_msgs::msg::PeriStatus>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<genie_msgs::msg::PeriStatus>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // GENIE_MSGS__MSG__DETAIL__PERI_STATUS__TRAITS_HPP_
