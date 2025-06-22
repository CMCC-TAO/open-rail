// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from genie_msgs:msg/CalibrateStatus.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__CALIBRATE_STATUS__TRAITS_HPP_
#define GENIE_MSGS__MSG__DETAIL__CALIBRATE_STATUS__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "genie_msgs/msg/detail/calibrate_status__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace genie_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const CalibrateStatus & msg,
  std::ostream & out)
{
  (void)msg;
  out << "null";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const CalibrateStatus & msg,
  std::ostream & out, size_t indentation = 0)
{
  (void)msg;
  (void)indentation;
  out << "null\n";
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const CalibrateStatus & msg, bool use_flow_style = false)
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
  const genie_msgs::msg::CalibrateStatus & msg,
  std::ostream & out, size_t indentation = 0)
{
  genie_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use genie_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const genie_msgs::msg::CalibrateStatus & msg)
{
  return genie_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<genie_msgs::msg::CalibrateStatus>()
{
  return "genie_msgs::msg::CalibrateStatus";
}

template<>
inline const char * name<genie_msgs::msg::CalibrateStatus>()
{
  return "genie_msgs/msg/CalibrateStatus";
}

template<>
struct has_fixed_size<genie_msgs::msg::CalibrateStatus>
  : std::integral_constant<bool, true> {};

template<>
struct has_bounded_size<genie_msgs::msg::CalibrateStatus>
  : std::integral_constant<bool, true> {};

template<>
struct is_message<genie_msgs::msg::CalibrateStatus>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // GENIE_MSGS__MSG__DETAIL__CALIBRATE_STATUS__TRAITS_HPP_
