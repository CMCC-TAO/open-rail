// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from genie_msgs:msg/FimArm.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FIM_ARM__TRAITS_HPP_
#define GENIE_MSGS__MSG__DETAIL__FIM_ARM__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "genie_msgs/msg/detail/fim_arm__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"

namespace genie_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const FimArm & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: fim_arm
  {
    if (msg.fim_arm.size() == 0) {
      out << "fim_arm: []";
    } else {
      out << "fim_arm: [";
      size_t pending_items = msg.fim_arm.size();
      for (auto item : msg.fim_arm) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: arm_err_code
  {
    if (msg.arm_err_code.size() == 0) {
      out << "arm_err_code: []";
    } else {
      out << "arm_err_code: [";
      size_t pending_items = msg.arm_err_code.size();
      for (auto item : msg.arm_err_code) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const FimArm & msg,
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

  // member: fim_arm
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.fim_arm.size() == 0) {
      out << "fim_arm: []\n";
    } else {
      out << "fim_arm:\n";
      for (auto item : msg.fim_arm) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }

  // member: arm_err_code
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.arm_err_code.size() == 0) {
      out << "arm_err_code: []\n";
    } else {
      out << "arm_err_code:\n";
      for (auto item : msg.arm_err_code) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const FimArm & msg, bool use_flow_style = false)
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
  const genie_msgs::msg::FimArm & msg,
  std::ostream & out, size_t indentation = 0)
{
  genie_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use genie_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const genie_msgs::msg::FimArm & msg)
{
  return genie_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<genie_msgs::msg::FimArm>()
{
  return "genie_msgs::msg::FimArm";
}

template<>
inline const char * name<genie_msgs::msg::FimArm>()
{
  return "genie_msgs/msg/FimArm";
}

template<>
struct has_fixed_size<genie_msgs::msg::FimArm>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<genie_msgs::msg::FimArm>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<genie_msgs::msg::FimArm>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // GENIE_MSGS__MSG__DETAIL__FIM_ARM__TRAITS_HPP_
