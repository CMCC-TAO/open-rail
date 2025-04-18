// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from genie_msgs:msg/AGVDetect.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__AGV_DETECT__TRAITS_HPP_
#define GENIE_MSGS__MSG__DETAIL__AGV_DETECT__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "genie_msgs/msg/detail/agv_detect__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"

namespace genie_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const AGVDetect & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: status
  {
    out << "status: ";
    rosidl_generator_traits::value_to_yaml(msg.status, out);
    out << ", ";
  }

  // member: err_code
  {
    out << "err_code: ";
    rosidl_generator_traits::value_to_yaml(msg.err_code, out);
    out << ", ";
  }

  // member: obs_valid
  {
    out << "obs_valid: ";
    rosidl_generator_traits::value_to_yaml(msg.obs_valid, out);
    out << ", ";
  }

  // member: obs_conf
  {
    out << "obs_conf: ";
    rosidl_generator_traits::value_to_yaml(msg.obs_conf, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const AGVDetect & msg,
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

  // member: status
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "status: ";
    rosidl_generator_traits::value_to_yaml(msg.status, out);
    out << "\n";
  }

  // member: err_code
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "err_code: ";
    rosidl_generator_traits::value_to_yaml(msg.err_code, out);
    out << "\n";
  }

  // member: obs_valid
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "obs_valid: ";
    rosidl_generator_traits::value_to_yaml(msg.obs_valid, out);
    out << "\n";
  }

  // member: obs_conf
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "obs_conf: ";
    rosidl_generator_traits::value_to_yaml(msg.obs_conf, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const AGVDetect & msg, bool use_flow_style = false)
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
  const genie_msgs::msg::AGVDetect & msg,
  std::ostream & out, size_t indentation = 0)
{
  genie_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use genie_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const genie_msgs::msg::AGVDetect & msg)
{
  return genie_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<genie_msgs::msg::AGVDetect>()
{
  return "genie_msgs::msg::AGVDetect";
}

template<>
inline const char * name<genie_msgs::msg::AGVDetect>()
{
  return "genie_msgs/msg/AGVDetect";
}

template<>
struct has_fixed_size<genie_msgs::msg::AGVDetect>
  : std::integral_constant<bool, has_fixed_size<std_msgs::msg::Header>::value> {};

template<>
struct has_bounded_size<genie_msgs::msg::AGVDetect>
  : std::integral_constant<bool, has_bounded_size<std_msgs::msg::Header>::value> {};

template<>
struct is_message<genie_msgs::msg::AGVDetect>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // GENIE_MSGS__MSG__DETAIL__AGV_DETECT__TRAITS_HPP_
