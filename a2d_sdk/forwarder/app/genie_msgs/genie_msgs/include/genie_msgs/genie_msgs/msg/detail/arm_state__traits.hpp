// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from genie_msgs:msg/ArmState.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__ARM_STATE__TRAITS_HPP_
#define GENIE_MSGS__MSG__DETAIL__ARM_STATE__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "genie_msgs/msg/detail/arm_state__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"
// Member 'motor_states'
#include "genie_msgs/msg/detail/motor_state__traits.hpp"

namespace genie_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const ArmState & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: motor_states
  {
    if (msg.motor_states.size() == 0) {
      out << "motor_states: []";
    } else {
      out << "motor_states: [";
      size_t pending_items = msg.motor_states.size();
      for (auto item : msg.motor_states) {
        to_flow_style_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: force_data
  {
    if (msg.force_data.size() == 0) {
      out << "force_data: []";
    } else {
      out << "force_data: [";
      size_t pending_items = msg.force_data.size();
      for (auto item : msg.force_data) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: force_coordinate
  {
    out << "force_coordinate: ";
    rosidl_generator_traits::value_to_yaml(msg.force_coordinate, out);
    out << ", ";
  }

  // member: force_state
  {
    out << "force_state: ";
    rosidl_generator_traits::value_to_yaml(msg.force_state, out);
    out << ", ";
  }

  // member: arm_state
  {
    out << "arm_state: ";
    rosidl_generator_traits::value_to_yaml(msg.arm_state, out);
    out << ", ";
  }

  // member: system_error
  {
    out << "system_error: ";
    rosidl_generator_traits::value_to_yaml(msg.system_error, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const ArmState & msg,
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

  // member: motor_states
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.motor_states.size() == 0) {
      out << "motor_states: []\n";
    } else {
      out << "motor_states:\n";
      for (auto item : msg.motor_states) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "-\n";
        to_block_style_yaml(item, out, indentation + 2);
      }
    }
  }

  // member: force_data
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.force_data.size() == 0) {
      out << "force_data: []\n";
    } else {
      out << "force_data:\n";
      for (auto item : msg.force_data) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }

  // member: force_coordinate
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "force_coordinate: ";
    rosidl_generator_traits::value_to_yaml(msg.force_coordinate, out);
    out << "\n";
  }

  // member: force_state
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "force_state: ";
    rosidl_generator_traits::value_to_yaml(msg.force_state, out);
    out << "\n";
  }

  // member: arm_state
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "arm_state: ";
    rosidl_generator_traits::value_to_yaml(msg.arm_state, out);
    out << "\n";
  }

  // member: system_error
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "system_error: ";
    rosidl_generator_traits::value_to_yaml(msg.system_error, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const ArmState & msg, bool use_flow_style = false)
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
  const genie_msgs::msg::ArmState & msg,
  std::ostream & out, size_t indentation = 0)
{
  genie_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use genie_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const genie_msgs::msg::ArmState & msg)
{
  return genie_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<genie_msgs::msg::ArmState>()
{
  return "genie_msgs::msg::ArmState";
}

template<>
inline const char * name<genie_msgs::msg::ArmState>()
{
  return "genie_msgs/msg/ArmState";
}

template<>
struct has_fixed_size<genie_msgs::msg::ArmState>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<genie_msgs::msg::ArmState>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<genie_msgs::msg::ArmState>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // GENIE_MSGS__MSG__DETAIL__ARM_STATE__TRAITS_HPP_
