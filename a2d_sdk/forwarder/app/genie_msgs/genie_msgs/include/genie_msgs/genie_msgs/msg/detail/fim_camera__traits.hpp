// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from genie_msgs:msg/FimCamera.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FIM_CAMERA__TRAITS_HPP_
#define GENIE_MSGS__MSG__DETAIL__FIM_CAMERA__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "genie_msgs/msg/detail/fim_camera__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"

namespace genie_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const FimCamera & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: fim_camera
  {
    if (msg.fim_camera.size() == 0) {
      out << "fim_camera: []";
    } else {
      out << "fim_camera: [";
      size_t pending_items = msg.fim_camera.size();
      for (auto item : msg.fim_camera) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: camera_name
  {
    if (msg.camera_name.size() == 0) {
      out << "camera_name: []";
    } else {
      out << "camera_name: [";
      size_t pending_items = msg.camera_name.size();
      for (auto item : msg.camera_name) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: err_code
  {
    if (msg.err_code.size() == 0) {
      out << "err_code: []";
    } else {
      out << "err_code: [";
      size_t pending_items = msg.err_code.size();
      for (auto item : msg.err_code) {
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
  const FimCamera & msg,
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

  // member: fim_camera
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.fim_camera.size() == 0) {
      out << "fim_camera: []\n";
    } else {
      out << "fim_camera:\n";
      for (auto item : msg.fim_camera) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }

  // member: camera_name
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.camera_name.size() == 0) {
      out << "camera_name: []\n";
    } else {
      out << "camera_name:\n";
      for (auto item : msg.camera_name) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }

  // member: err_code
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.err_code.size() == 0) {
      out << "err_code: []\n";
    } else {
      out << "err_code:\n";
      for (auto item : msg.err_code) {
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

inline std::string to_yaml(const FimCamera & msg, bool use_flow_style = false)
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
  const genie_msgs::msg::FimCamera & msg,
  std::ostream & out, size_t indentation = 0)
{
  genie_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use genie_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const genie_msgs::msg::FimCamera & msg)
{
  return genie_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<genie_msgs::msg::FimCamera>()
{
  return "genie_msgs::msg::FimCamera";
}

template<>
inline const char * name<genie_msgs::msg::FimCamera>()
{
  return "genie_msgs/msg/FimCamera";
}

template<>
struct has_fixed_size<genie_msgs::msg::FimCamera>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<genie_msgs::msg::FimCamera>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<genie_msgs::msg::FimCamera>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // GENIE_MSGS__MSG__DETAIL__FIM_CAMERA__TRAITS_HPP_
