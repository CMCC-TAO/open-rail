// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from genie_msgs:msg/EndState.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__END_STATE__TRAITS_HPP_
#define GENIE_MSGS__MSG__DETAIL__END_STATE__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "genie_msgs/msg/detail/end_state__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"
// Member 'end_state'
#include "genie_msgs/msg/detail/motor_state__traits.hpp"

namespace genie_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const EndState & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: controlled
  {
    out << "controlled: ";
    rosidl_generator_traits::value_to_yaml(msg.controlled, out);
    out << ", ";
  }

  // member: end_state
  {
    if (msg.end_state.size() == 0) {
      out << "end_state: []";
    } else {
      out << "end_state: [";
      size_t pending_items = msg.end_state.size();
      for (auto item : msg.end_state) {
        to_flow_style_yaml(item, out);
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
  const EndState & msg,
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

  // member: controlled
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "controlled: ";
    rosidl_generator_traits::value_to_yaml(msg.controlled, out);
    out << "\n";
  }

  // member: end_state
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.end_state.size() == 0) {
      out << "end_state: []\n";
    } else {
      out << "end_state:\n";
      for (auto item : msg.end_state) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "-\n";
        to_block_style_yaml(item, out, indentation + 2);
      }
    }
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const EndState & msg, bool use_flow_style = false)
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
  const genie_msgs::msg::EndState & msg,
  std::ostream & out, size_t indentation = 0)
{
  genie_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use genie_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const genie_msgs::msg::EndState & msg)
{
  return genie_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<genie_msgs::msg::EndState>()
{
  return "genie_msgs::msg::EndState";
}

template<>
inline const char * name<genie_msgs::msg::EndState>()
{
  return "genie_msgs/msg/EndState";
}

template<>
struct has_fixed_size<genie_msgs::msg::EndState>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<genie_msgs::msg::EndState>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<genie_msgs::msg::EndState>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // GENIE_MSGS__MSG__DETAIL__END_STATE__TRAITS_HPP_
