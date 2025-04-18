// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from genie_msgs:msg/FimEE.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FIM_EE__TRAITS_HPP_
#define GENIE_MSGS__MSG__DETAIL__FIM_EE__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "genie_msgs/msg/detail/fim_ee__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"

namespace genie_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const FimEE & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: fim_ee
  {
    if (msg.fim_ee.size() == 0) {
      out << "fim_ee: []";
    } else {
      out << "fim_ee: [";
      size_t pending_items = msg.fim_ee.size();
      for (auto item : msg.fim_ee) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: ee_err_code
  {
    if (msg.ee_err_code.size() == 0) {
      out << "ee_err_code: []";
    } else {
      out << "ee_err_code: [";
      size_t pending_items = msg.ee_err_code.size();
      for (auto item : msg.ee_err_code) {
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
  const FimEE & msg,
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

  // member: fim_ee
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.fim_ee.size() == 0) {
      out << "fim_ee: []\n";
    } else {
      out << "fim_ee:\n";
      for (auto item : msg.fim_ee) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }

  // member: ee_err_code
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.ee_err_code.size() == 0) {
      out << "ee_err_code: []\n";
    } else {
      out << "ee_err_code:\n";
      for (auto item : msg.ee_err_code) {
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

inline std::string to_yaml(const FimEE & msg, bool use_flow_style = false)
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
  const genie_msgs::msg::FimEE & msg,
  std::ostream & out, size_t indentation = 0)
{
  genie_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use genie_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const genie_msgs::msg::FimEE & msg)
{
  return genie_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<genie_msgs::msg::FimEE>()
{
  return "genie_msgs::msg::FimEE";
}

template<>
inline const char * name<genie_msgs::msg::FimEE>()
{
  return "genie_msgs/msg/FimEE";
}

template<>
struct has_fixed_size<genie_msgs::msg::FimEE>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<genie_msgs::msg::FimEE>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<genie_msgs::msg::FimEE>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // GENIE_MSGS__MSG__DETAIL__FIM_EE__TRAITS_HPP_
