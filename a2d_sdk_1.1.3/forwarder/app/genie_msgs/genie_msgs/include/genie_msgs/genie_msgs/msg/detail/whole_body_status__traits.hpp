// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from genie_msgs:msg/WholeBodyStatus.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__WHOLE_BODY_STATUS__TRAITS_HPP_
#define GENIE_MSGS__MSG__DETAIL__WHOLE_BODY_STATUS__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "genie_msgs/msg/detail/whole_body_status__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"

namespace genie_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const WholeBodyStatus & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: right_arm_error
  {
    out << "right_arm_error: ";
    rosidl_generator_traits::value_to_yaml(msg.right_arm_error, out);
    out << ", ";
  }

  // member: left_arm_error
  {
    out << "left_arm_error: ";
    rosidl_generator_traits::value_to_yaml(msg.left_arm_error, out);
    out << ", ";
  }

  // member: right_arm_control
  {
    out << "right_arm_control: ";
    rosidl_generator_traits::value_to_yaml(msg.right_arm_control, out);
    out << ", ";
  }

  // member: left_arm_control
  {
    out << "left_arm_control: ";
    rosidl_generator_traits::value_to_yaml(msg.left_arm_control, out);
    out << ", ";
  }

  // member: right_arm_estop
  {
    out << "right_arm_estop: ";
    rosidl_generator_traits::value_to_yaml(msg.right_arm_estop, out);
    out << ", ";
  }

  // member: left_arm_estop
  {
    out << "left_arm_estop: ";
    rosidl_generator_traits::value_to_yaml(msg.left_arm_estop, out);
    out << ", ";
  }

  // member: right_end_error
  {
    out << "right_end_error: ";
    rosidl_generator_traits::value_to_yaml(msg.right_end_error, out);
    out << ", ";
  }

  // member: left_end_error
  {
    out << "left_end_error: ";
    rosidl_generator_traits::value_to_yaml(msg.left_end_error, out);
    out << ", ";
  }

  // member: waist_error
  {
    out << "waist_error: ";
    rosidl_generator_traits::value_to_yaml(msg.waist_error, out);
    out << ", ";
  }

  // member: lift_error
  {
    out << "lift_error: ";
    rosidl_generator_traits::value_to_yaml(msg.lift_error, out);
    out << ", ";
  }

  // member: neck_error
  {
    out << "neck_error: ";
    rosidl_generator_traits::value_to_yaml(msg.neck_error, out);
    out << ", ";
  }

  // member: chassis_error
  {
    out << "chassis_error: ";
    rosidl_generator_traits::value_to_yaml(msg.chassis_error, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const WholeBodyStatus & msg,
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

  // member: right_arm_error
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "right_arm_error: ";
    rosidl_generator_traits::value_to_yaml(msg.right_arm_error, out);
    out << "\n";
  }

  // member: left_arm_error
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "left_arm_error: ";
    rosidl_generator_traits::value_to_yaml(msg.left_arm_error, out);
    out << "\n";
  }

  // member: right_arm_control
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "right_arm_control: ";
    rosidl_generator_traits::value_to_yaml(msg.right_arm_control, out);
    out << "\n";
  }

  // member: left_arm_control
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "left_arm_control: ";
    rosidl_generator_traits::value_to_yaml(msg.left_arm_control, out);
    out << "\n";
  }

  // member: right_arm_estop
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "right_arm_estop: ";
    rosidl_generator_traits::value_to_yaml(msg.right_arm_estop, out);
    out << "\n";
  }

  // member: left_arm_estop
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "left_arm_estop: ";
    rosidl_generator_traits::value_to_yaml(msg.left_arm_estop, out);
    out << "\n";
  }

  // member: right_end_error
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "right_end_error: ";
    rosidl_generator_traits::value_to_yaml(msg.right_end_error, out);
    out << "\n";
  }

  // member: left_end_error
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "left_end_error: ";
    rosidl_generator_traits::value_to_yaml(msg.left_end_error, out);
    out << "\n";
  }

  // member: waist_error
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "waist_error: ";
    rosidl_generator_traits::value_to_yaml(msg.waist_error, out);
    out << "\n";
  }

  // member: lift_error
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "lift_error: ";
    rosidl_generator_traits::value_to_yaml(msg.lift_error, out);
    out << "\n";
  }

  // member: neck_error
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "neck_error: ";
    rosidl_generator_traits::value_to_yaml(msg.neck_error, out);
    out << "\n";
  }

  // member: chassis_error
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "chassis_error: ";
    rosidl_generator_traits::value_to_yaml(msg.chassis_error, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const WholeBodyStatus & msg, bool use_flow_style = false)
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
  const genie_msgs::msg::WholeBodyStatus & msg,
  std::ostream & out, size_t indentation = 0)
{
  genie_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use genie_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const genie_msgs::msg::WholeBodyStatus & msg)
{
  return genie_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<genie_msgs::msg::WholeBodyStatus>()
{
  return "genie_msgs::msg::WholeBodyStatus";
}

template<>
inline const char * name<genie_msgs::msg::WholeBodyStatus>()
{
  return "genie_msgs/msg/WholeBodyStatus";
}

template<>
struct has_fixed_size<genie_msgs::msg::WholeBodyStatus>
  : std::integral_constant<bool, has_fixed_size<std_msgs::msg::Header>::value> {};

template<>
struct has_bounded_size<genie_msgs::msg::WholeBodyStatus>
  : std::integral_constant<bool, has_bounded_size<std_msgs::msg::Header>::value> {};

template<>
struct is_message<genie_msgs::msg::WholeBodyStatus>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // GENIE_MSGS__MSG__DETAIL__WHOLE_BODY_STATUS__TRAITS_HPP_
