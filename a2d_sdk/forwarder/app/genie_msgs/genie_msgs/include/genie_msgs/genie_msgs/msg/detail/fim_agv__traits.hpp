// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from genie_msgs:msg/FimAGV.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FIM_AGV__TRAITS_HPP_
#define GENIE_MSGS__MSG__DETAIL__FIM_AGV__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "genie_msgs/msg/detail/fim_agv__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"

namespace genie_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const FimAGV & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: fim_agv
  {
    out << "fim_agv: ";
    rosidl_generator_traits::value_to_yaml(msg.fim_agv, out);
    out << ", ";
  }

  // member: agv_err_code
  {
    out << "agv_err_code: ";
    rosidl_generator_traits::value_to_yaml(msg.agv_err_code, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const FimAGV & msg,
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

  // member: fim_agv
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "fim_agv: ";
    rosidl_generator_traits::value_to_yaml(msg.fim_agv, out);
    out << "\n";
  }

  // member: agv_err_code
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "agv_err_code: ";
    rosidl_generator_traits::value_to_yaml(msg.agv_err_code, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const FimAGV & msg, bool use_flow_style = false)
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
  const genie_msgs::msg::FimAGV & msg,
  std::ostream & out, size_t indentation = 0)
{
  genie_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use genie_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const genie_msgs::msg::FimAGV & msg)
{
  return genie_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<genie_msgs::msg::FimAGV>()
{
  return "genie_msgs::msg::FimAGV";
}

template<>
inline const char * name<genie_msgs::msg::FimAGV>()
{
  return "genie_msgs/msg/FimAGV";
}

template<>
struct has_fixed_size<genie_msgs::msg::FimAGV>
  : std::integral_constant<bool, has_fixed_size<std_msgs::msg::Header>::value> {};

template<>
struct has_bounded_size<genie_msgs::msg::FimAGV>
  : std::integral_constant<bool, has_bounded_size<std_msgs::msg::Header>::value> {};

template<>
struct is_message<genie_msgs::msg::FimAGV>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // GENIE_MSGS__MSG__DETAIL__FIM_AGV__TRAITS_HPP_
