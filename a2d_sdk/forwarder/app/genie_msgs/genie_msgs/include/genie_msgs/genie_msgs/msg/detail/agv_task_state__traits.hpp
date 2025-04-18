// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from genie_msgs:msg/AGVTaskState.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__AGV_TASK_STATE__TRAITS_HPP_
#define GENIE_MSGS__MSG__DETAIL__AGV_TASK_STATE__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "genie_msgs/msg/detail/agv_task_state__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"

namespace genie_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const AGVTaskState & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: task_uuid
  {
    out << "task_uuid: ";
    rosidl_generator_traits::value_to_yaml(msg.task_uuid, out);
    out << ", ";
  }

  // member: task_reqid
  {
    out << "task_reqid: ";
    rosidl_generator_traits::value_to_yaml(msg.task_reqid, out);
    out << ", ";
  }

  // member: curr_station_idx
  {
    out << "curr_station_idx: ";
    rosidl_generator_traits::value_to_yaml(msg.curr_station_idx, out);
    out << ", ";
  }

  // member: finish_state
  {
    out << "finish_state: ";
    rosidl_generator_traits::value_to_yaml(msg.finish_state, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const AGVTaskState & msg,
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

  // member: task_uuid
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "task_uuid: ";
    rosidl_generator_traits::value_to_yaml(msg.task_uuid, out);
    out << "\n";
  }

  // member: task_reqid
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "task_reqid: ";
    rosidl_generator_traits::value_to_yaml(msg.task_reqid, out);
    out << "\n";
  }

  // member: curr_station_idx
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "curr_station_idx: ";
    rosidl_generator_traits::value_to_yaml(msg.curr_station_idx, out);
    out << "\n";
  }

  // member: finish_state
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "finish_state: ";
    rosidl_generator_traits::value_to_yaml(msg.finish_state, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const AGVTaskState & msg, bool use_flow_style = false)
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
  const genie_msgs::msg::AGVTaskState & msg,
  std::ostream & out, size_t indentation = 0)
{
  genie_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use genie_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const genie_msgs::msg::AGVTaskState & msg)
{
  return genie_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<genie_msgs::msg::AGVTaskState>()
{
  return "genie_msgs::msg::AGVTaskState";
}

template<>
inline const char * name<genie_msgs::msg::AGVTaskState>()
{
  return "genie_msgs/msg/AGVTaskState";
}

template<>
struct has_fixed_size<genie_msgs::msg::AGVTaskState>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<genie_msgs::msg::AGVTaskState>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<genie_msgs::msg::AGVTaskState>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // GENIE_MSGS__MSG__DETAIL__AGV_TASK_STATE__TRAITS_HPP_
