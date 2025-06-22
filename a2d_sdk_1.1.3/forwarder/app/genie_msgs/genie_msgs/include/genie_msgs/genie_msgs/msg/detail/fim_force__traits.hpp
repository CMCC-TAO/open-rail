// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from genie_msgs:msg/FimForce.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FIM_FORCE__TRAITS_HPP_
#define GENIE_MSGS__MSG__DETAIL__FIM_FORCE__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "genie_msgs/msg/detail/fim_force__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"

namespace genie_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const FimForce & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: fim_force
  {
    if (msg.fim_force.size() == 0) {
      out << "fim_force: []";
    } else {
      out << "fim_force: [";
      size_t pending_items = msg.fim_force.size();
      for (auto item : msg.fim_force) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: force_err_code
  {
    if (msg.force_err_code.size() == 0) {
      out << "force_err_code: []";
    } else {
      out << "force_err_code: [";
      size_t pending_items = msg.force_err_code.size();
      for (auto item : msg.force_err_code) {
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
  const FimForce & msg,
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

  // member: fim_force
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.fim_force.size() == 0) {
      out << "fim_force: []\n";
    } else {
      out << "fim_force:\n";
      for (auto item : msg.fim_force) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }

  // member: force_err_code
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.force_err_code.size() == 0) {
      out << "force_err_code: []\n";
    } else {
      out << "force_err_code:\n";
      for (auto item : msg.force_err_code) {
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

inline std::string to_yaml(const FimForce & msg, bool use_flow_style = false)
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
  const genie_msgs::msg::FimForce & msg,
  std::ostream & out, size_t indentation = 0)
{
  genie_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use genie_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const genie_msgs::msg::FimForce & msg)
{
  return genie_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<genie_msgs::msg::FimForce>()
{
  return "genie_msgs::msg::FimForce";
}

template<>
inline const char * name<genie_msgs::msg::FimForce>()
{
  return "genie_msgs/msg/FimForce";
}

template<>
struct has_fixed_size<genie_msgs::msg::FimForce>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<genie_msgs::msg::FimForce>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<genie_msgs::msg::FimForce>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // GENIE_MSGS__MSG__DETAIL__FIM_FORCE__TRAITS_HPP_
