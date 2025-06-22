// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from genie_msgs:msg/FimFirmware.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FIM_FIRMWARE__TRAITS_HPP_
#define GENIE_MSGS__MSG__DETAIL__FIM_FIRMWARE__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "genie_msgs/msg/detail/fim_firmware__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"

namespace genie_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const FimFirmware & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: fim_fw
  {
    out << "fim_fw: ";
    rosidl_generator_traits::value_to_yaml(msg.fim_fw, out);
    out << ", ";
  }

  // member: err_code_byte
  {
    out << "err_code_byte: ";
    rosidl_generator_traits::value_to_yaml(msg.err_code_byte, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const FimFirmware & msg,
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

  // member: fim_fw
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "fim_fw: ";
    rosidl_generator_traits::value_to_yaml(msg.fim_fw, out);
    out << "\n";
  }

  // member: err_code_byte
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "err_code_byte: ";
    rosidl_generator_traits::value_to_yaml(msg.err_code_byte, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const FimFirmware & msg, bool use_flow_style = false)
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
  const genie_msgs::msg::FimFirmware & msg,
  std::ostream & out, size_t indentation = 0)
{
  genie_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use genie_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const genie_msgs::msg::FimFirmware & msg)
{
  return genie_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<genie_msgs::msg::FimFirmware>()
{
  return "genie_msgs::msg::FimFirmware";
}

template<>
inline const char * name<genie_msgs::msg::FimFirmware>()
{
  return "genie_msgs/msg/FimFirmware";
}

template<>
struct has_fixed_size<genie_msgs::msg::FimFirmware>
  : std::integral_constant<bool, has_fixed_size<std_msgs::msg::Header>::value> {};

template<>
struct has_bounded_size<genie_msgs::msg::FimFirmware>
  : std::integral_constant<bool, has_bounded_size<std_msgs::msg::Header>::value> {};

template<>
struct is_message<genie_msgs::msg::FimFirmware>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // GENIE_MSGS__MSG__DETAIL__FIM_FIRMWARE__TRAITS_HPP_
