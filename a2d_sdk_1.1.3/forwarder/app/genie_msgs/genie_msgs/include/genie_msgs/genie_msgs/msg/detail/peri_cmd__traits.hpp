// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from genie_msgs:msg/PeriCmd.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__PERI_CMD__TRAITS_HPP_
#define GENIE_MSGS__MSG__DETAIL__PERI_CMD__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "genie_msgs/msg/detail/peri_cmd__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"

namespace genie_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const PeriCmd & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: compute_center_ready_shut_down
  {
    out << "compute_center_ready_shut_down: ";
    rosidl_generator_traits::value_to_yaml(msg.compute_center_ready_shut_down, out);
    out << ", ";
  }

  // member: soft_emergency_stop
  {
    out << "soft_emergency_stop: ";
    rosidl_generator_traits::value_to_yaml(msg.soft_emergency_stop, out);
    out << ", ";
  }

  // member: hub1_reset_request
  {
    out << "hub1_reset_request: ";
    rosidl_generator_traits::value_to_yaml(msg.hub1_reset_request, out);
    out << ", ";
  }

  // member: hub2_reset_request
  {
    out << "hub2_reset_request: ";
    rosidl_generator_traits::value_to_yaml(msg.hub2_reset_request, out);
    out << ", ";
  }

  // member: left_arm_reset_request
  {
    out << "left_arm_reset_request: ";
    rosidl_generator_traits::value_to_yaml(msg.left_arm_reset_request, out);
    out << ", ";
  }

  // member: right_arm_reset_request
  {
    out << "right_arm_reset_request: ";
    rosidl_generator_traits::value_to_yaml(msg.right_arm_reset_request, out);
    out << ", ";
  }

  // member: left_end_reset_request
  {
    out << "left_end_reset_request: ";
    rosidl_generator_traits::value_to_yaml(msg.left_end_reset_request, out);
    out << ", ";
  }

  // member: right_end_reset_request
  {
    out << "right_end_reset_request: ";
    rosidl_generator_traits::value_to_yaml(msg.right_end_reset_request, out);
    out << ", ";
  }

  // member: waist_pitch_motor_reset_request
  {
    out << "waist_pitch_motor_reset_request: ";
    rosidl_generator_traits::value_to_yaml(msg.waist_pitch_motor_reset_request, out);
    out << ", ";
  }

  // member: lift_motor_reset_request
  {
    out << "lift_motor_reset_request: ";
    rosidl_generator_traits::value_to_yaml(msg.lift_motor_reset_request, out);
    out << ", ";
  }

  // member: head_yaw_motor_reset_request
  {
    out << "head_yaw_motor_reset_request: ";
    rosidl_generator_traits::value_to_yaml(msg.head_yaw_motor_reset_request, out);
    out << ", ";
  }

  // member: head_pitch_motor_reset_request
  {
    out << "head_pitch_motor_reset_request: ";
    rosidl_generator_traits::value_to_yaml(msg.head_pitch_motor_reset_request, out);
    out << ", ";
  }

  // member: agv_reset_request
  {
    out << "agv_reset_request: ";
    rosidl_generator_traits::value_to_yaml(msg.agv_reset_request, out);
    out << ", ";
  }

  // member: work_mode
  {
    out << "work_mode: ";
    rosidl_generator_traits::value_to_yaml(msg.work_mode, out);
    out << ", ";
  }

  // member: feature_status
  {
    out << "feature_status: ";
    rosidl_generator_traits::value_to_yaml(msg.feature_status, out);
    out << ", ";
  }

  // member: left_arm_power_ctrl_req
  {
    out << "left_arm_power_ctrl_req: ";
    rosidl_generator_traits::value_to_yaml(msg.left_arm_power_ctrl_req, out);
    out << ", ";
  }

  // member: right_arm_power_ctrl_req
  {
    out << "right_arm_power_ctrl_req: ";
    rosidl_generator_traits::value_to_yaml(msg.right_arm_power_ctrl_req, out);
    out << ", ";
  }

  // member: left_end_power_ctrl_req
  {
    out << "left_end_power_ctrl_req: ";
    rosidl_generator_traits::value_to_yaml(msg.left_end_power_ctrl_req, out);
    out << ", ";
  }

  // member: right_end_power_ctrl_req
  {
    out << "right_end_power_ctrl_req: ";
    rosidl_generator_traits::value_to_yaml(msg.right_end_power_ctrl_req, out);
    out << ", ";
  }

  // member: waist_pitch_motor_power_ctrl_req
  {
    out << "waist_pitch_motor_power_ctrl_req: ";
    rosidl_generator_traits::value_to_yaml(msg.waist_pitch_motor_power_ctrl_req, out);
    out << ", ";
  }

  // member: lift_motor_power_ctrl_req
  {
    out << "lift_motor_power_ctrl_req: ";
    rosidl_generator_traits::value_to_yaml(msg.lift_motor_power_ctrl_req, out);
    out << ", ";
  }

  // member: head_yaw_motor_power_ctrl_req
  {
    out << "head_yaw_motor_power_ctrl_req: ";
    rosidl_generator_traits::value_to_yaml(msg.head_yaw_motor_power_ctrl_req, out);
    out << ", ";
  }

  // member: head_pitch_motor_power_ctrl_req
  {
    out << "head_pitch_motor_power_ctrl_req: ";
    rosidl_generator_traits::value_to_yaml(msg.head_pitch_motor_power_ctrl_req, out);
    out << ", ";
  }

  // member: agv_power_ctrl_req
  {
    out << "agv_power_ctrl_req: ";
    rosidl_generator_traits::value_to_yaml(msg.agv_power_ctrl_req, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const PeriCmd & msg,
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

  // member: compute_center_ready_shut_down
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "compute_center_ready_shut_down: ";
    rosidl_generator_traits::value_to_yaml(msg.compute_center_ready_shut_down, out);
    out << "\n";
  }

  // member: soft_emergency_stop
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "soft_emergency_stop: ";
    rosidl_generator_traits::value_to_yaml(msg.soft_emergency_stop, out);
    out << "\n";
  }

  // member: hub1_reset_request
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "hub1_reset_request: ";
    rosidl_generator_traits::value_to_yaml(msg.hub1_reset_request, out);
    out << "\n";
  }

  // member: hub2_reset_request
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "hub2_reset_request: ";
    rosidl_generator_traits::value_to_yaml(msg.hub2_reset_request, out);
    out << "\n";
  }

  // member: left_arm_reset_request
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "left_arm_reset_request: ";
    rosidl_generator_traits::value_to_yaml(msg.left_arm_reset_request, out);
    out << "\n";
  }

  // member: right_arm_reset_request
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "right_arm_reset_request: ";
    rosidl_generator_traits::value_to_yaml(msg.right_arm_reset_request, out);
    out << "\n";
  }

  // member: left_end_reset_request
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "left_end_reset_request: ";
    rosidl_generator_traits::value_to_yaml(msg.left_end_reset_request, out);
    out << "\n";
  }

  // member: right_end_reset_request
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "right_end_reset_request: ";
    rosidl_generator_traits::value_to_yaml(msg.right_end_reset_request, out);
    out << "\n";
  }

  // member: waist_pitch_motor_reset_request
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "waist_pitch_motor_reset_request: ";
    rosidl_generator_traits::value_to_yaml(msg.waist_pitch_motor_reset_request, out);
    out << "\n";
  }

  // member: lift_motor_reset_request
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "lift_motor_reset_request: ";
    rosidl_generator_traits::value_to_yaml(msg.lift_motor_reset_request, out);
    out << "\n";
  }

  // member: head_yaw_motor_reset_request
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "head_yaw_motor_reset_request: ";
    rosidl_generator_traits::value_to_yaml(msg.head_yaw_motor_reset_request, out);
    out << "\n";
  }

  // member: head_pitch_motor_reset_request
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "head_pitch_motor_reset_request: ";
    rosidl_generator_traits::value_to_yaml(msg.head_pitch_motor_reset_request, out);
    out << "\n";
  }

  // member: agv_reset_request
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "agv_reset_request: ";
    rosidl_generator_traits::value_to_yaml(msg.agv_reset_request, out);
    out << "\n";
  }

  // member: work_mode
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "work_mode: ";
    rosidl_generator_traits::value_to_yaml(msg.work_mode, out);
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

  // member: left_arm_power_ctrl_req
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "left_arm_power_ctrl_req: ";
    rosidl_generator_traits::value_to_yaml(msg.left_arm_power_ctrl_req, out);
    out << "\n";
  }

  // member: right_arm_power_ctrl_req
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "right_arm_power_ctrl_req: ";
    rosidl_generator_traits::value_to_yaml(msg.right_arm_power_ctrl_req, out);
    out << "\n";
  }

  // member: left_end_power_ctrl_req
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "left_end_power_ctrl_req: ";
    rosidl_generator_traits::value_to_yaml(msg.left_end_power_ctrl_req, out);
    out << "\n";
  }

  // member: right_end_power_ctrl_req
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "right_end_power_ctrl_req: ";
    rosidl_generator_traits::value_to_yaml(msg.right_end_power_ctrl_req, out);
    out << "\n";
  }

  // member: waist_pitch_motor_power_ctrl_req
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "waist_pitch_motor_power_ctrl_req: ";
    rosidl_generator_traits::value_to_yaml(msg.waist_pitch_motor_power_ctrl_req, out);
    out << "\n";
  }

  // member: lift_motor_power_ctrl_req
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "lift_motor_power_ctrl_req: ";
    rosidl_generator_traits::value_to_yaml(msg.lift_motor_power_ctrl_req, out);
    out << "\n";
  }

  // member: head_yaw_motor_power_ctrl_req
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "head_yaw_motor_power_ctrl_req: ";
    rosidl_generator_traits::value_to_yaml(msg.head_yaw_motor_power_ctrl_req, out);
    out << "\n";
  }

  // member: head_pitch_motor_power_ctrl_req
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "head_pitch_motor_power_ctrl_req: ";
    rosidl_generator_traits::value_to_yaml(msg.head_pitch_motor_power_ctrl_req, out);
    out << "\n";
  }

  // member: agv_power_ctrl_req
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "agv_power_ctrl_req: ";
    rosidl_generator_traits::value_to_yaml(msg.agv_power_ctrl_req, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const PeriCmd & msg, bool use_flow_style = false)
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
  const genie_msgs::msg::PeriCmd & msg,
  std::ostream & out, size_t indentation = 0)
{
  genie_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use genie_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const genie_msgs::msg::PeriCmd & msg)
{
  return genie_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<genie_msgs::msg::PeriCmd>()
{
  return "genie_msgs::msg::PeriCmd";
}

template<>
inline const char * name<genie_msgs::msg::PeriCmd>()
{
  return "genie_msgs/msg/PeriCmd";
}

template<>
struct has_fixed_size<genie_msgs::msg::PeriCmd>
  : std::integral_constant<bool, has_fixed_size<std_msgs::msg::Header>::value> {};

template<>
struct has_bounded_size<genie_msgs::msg::PeriCmd>
  : std::integral_constant<bool, has_bounded_size<std_msgs::msg::Header>::value> {};

template<>
struct is_message<genie_msgs::msg::PeriCmd>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // GENIE_MSGS__MSG__DETAIL__PERI_CMD__TRAITS_HPP_
