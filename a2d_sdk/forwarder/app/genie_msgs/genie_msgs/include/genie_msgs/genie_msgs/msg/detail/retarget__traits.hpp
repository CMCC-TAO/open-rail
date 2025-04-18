// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from genie_msgs:msg/Retarget.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__RETARGET__TRAITS_HPP_
#define GENIE_MSGS__MSG__DETAIL__RETARGET__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "genie_msgs/msg/detail/retarget__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"
// Member 'left_ee_pose'
// Member 'right_ee_pose'
// Member 'left_upper_arm'
// Member 'right_upper_arm'
#include "geometry_msgs/msg/detail/pose__traits.hpp"

namespace genie_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const Retarget & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: group_arms
  {
    out << "group_arms: ";
    rosidl_generator_traits::value_to_yaml(msg.group_arms, out);
    out << ", ";
  }

  // member: group_body
  {
    out << "group_body: ";
    rosidl_generator_traits::value_to_yaml(msg.group_body, out);
    out << ", ";
  }

  // member: device
  {
    out << "device: ";
    rosidl_generator_traits::value_to_yaml(msg.device, out);
    out << ", ";
  }

  // member: left_ee_pose
  {
    out << "left_ee_pose: ";
    to_flow_style_yaml(msg.left_ee_pose, out);
    out << ", ";
  }

  // member: right_ee_pose
  {
    out << "right_ee_pose: ";
    to_flow_style_yaml(msg.right_ee_pose, out);
    out << ", ";
  }

  // member: left_upper_arm
  {
    out << "left_upper_arm: ";
    to_flow_style_yaml(msg.left_upper_arm, out);
    out << ", ";
  }

  // member: right_upper_arm
  {
    out << "right_upper_arm: ";
    to_flow_style_yaml(msg.right_upper_arm, out);
    out << ", ";
  }

  // member: body_joint_names
  {
    if (msg.body_joint_names.size() == 0) {
      out << "body_joint_names: []";
    } else {
      out << "body_joint_names: [";
      size_t pending_items = msg.body_joint_names.size();
      for (auto item : msg.body_joint_names) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: body_joint_positions
  {
    if (msg.body_joint_positions.size() == 0) {
      out << "body_joint_positions: []";
    } else {
      out << "body_joint_positions: [";
      size_t pending_items = msg.body_joint_positions.size();
      for (auto item : msg.body_joint_positions) {
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
  const Retarget & msg,
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

  // member: group_arms
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "group_arms: ";
    rosidl_generator_traits::value_to_yaml(msg.group_arms, out);
    out << "\n";
  }

  // member: group_body
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "group_body: ";
    rosidl_generator_traits::value_to_yaml(msg.group_body, out);
    out << "\n";
  }

  // member: device
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "device: ";
    rosidl_generator_traits::value_to_yaml(msg.device, out);
    out << "\n";
  }

  // member: left_ee_pose
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "left_ee_pose:\n";
    to_block_style_yaml(msg.left_ee_pose, out, indentation + 2);
  }

  // member: right_ee_pose
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "right_ee_pose:\n";
    to_block_style_yaml(msg.right_ee_pose, out, indentation + 2);
  }

  // member: left_upper_arm
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "left_upper_arm:\n";
    to_block_style_yaml(msg.left_upper_arm, out, indentation + 2);
  }

  // member: right_upper_arm
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "right_upper_arm:\n";
    to_block_style_yaml(msg.right_upper_arm, out, indentation + 2);
  }

  // member: body_joint_names
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.body_joint_names.size() == 0) {
      out << "body_joint_names: []\n";
    } else {
      out << "body_joint_names:\n";
      for (auto item : msg.body_joint_names) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }

  // member: body_joint_positions
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.body_joint_positions.size() == 0) {
      out << "body_joint_positions: []\n";
    } else {
      out << "body_joint_positions:\n";
      for (auto item : msg.body_joint_positions) {
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

inline std::string to_yaml(const Retarget & msg, bool use_flow_style = false)
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
  const genie_msgs::msg::Retarget & msg,
  std::ostream & out, size_t indentation = 0)
{
  genie_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use genie_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const genie_msgs::msg::Retarget & msg)
{
  return genie_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<genie_msgs::msg::Retarget>()
{
  return "genie_msgs::msg::Retarget";
}

template<>
inline const char * name<genie_msgs::msg::Retarget>()
{
  return "genie_msgs/msg/Retarget";
}

template<>
struct has_fixed_size<genie_msgs::msg::Retarget>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<genie_msgs::msg::Retarget>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<genie_msgs::msg::Retarget>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // GENIE_MSGS__MSG__DETAIL__RETARGET__TRAITS_HPP_
