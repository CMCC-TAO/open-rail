// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from genie_msgs:msg/MocapNetwork.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__MOCAP_NETWORK__TRAITS_HPP_
#define GENIE_MSGS__MSG__DETAIL__MOCAP_NETWORK__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "genie_msgs/msg/detail/mocap_network__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"

namespace genie_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const MocapNetwork & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: device_name
  {
    out << "device_name: ";
    rosidl_generator_traits::value_to_yaml(msg.device_name, out);
    out << ", ";
  }

  // member: is_connected
  {
    out << "is_connected: ";
    rosidl_generator_traits::value_to_yaml(msg.is_connected, out);
    out << ", ";
  }

  // member: packet_loss_rate
  {
    out << "packet_loss_rate: ";
    rosidl_generator_traits::value_to_yaml(msg.packet_loss_rate, out);
    out << ", ";
  }

  // member: latency
  {
    out << "latency: ";
    rosidl_generator_traits::value_to_yaml(msg.latency, out);
    out << ", ";
  }

  // member: frequency
  {
    out << "frequency: ";
    rosidl_generator_traits::value_to_yaml(msg.frequency, out);
    out << ", ";
  }

  // member: ip_address
  {
    out << "ip_address: ";
    rosidl_generator_traits::value_to_yaml(msg.ip_address, out);
    out << ", ";
  }

  // member: remote_ip_address
  {
    out << "remote_ip_address: ";
    rosidl_generator_traits::value_to_yaml(msg.remote_ip_address, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const MocapNetwork & msg,
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

  // member: device_name
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "device_name: ";
    rosidl_generator_traits::value_to_yaml(msg.device_name, out);
    out << "\n";
  }

  // member: is_connected
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "is_connected: ";
    rosidl_generator_traits::value_to_yaml(msg.is_connected, out);
    out << "\n";
  }

  // member: packet_loss_rate
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "packet_loss_rate: ";
    rosidl_generator_traits::value_to_yaml(msg.packet_loss_rate, out);
    out << "\n";
  }

  // member: latency
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "latency: ";
    rosidl_generator_traits::value_to_yaml(msg.latency, out);
    out << "\n";
  }

  // member: frequency
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "frequency: ";
    rosidl_generator_traits::value_to_yaml(msg.frequency, out);
    out << "\n";
  }

  // member: ip_address
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "ip_address: ";
    rosidl_generator_traits::value_to_yaml(msg.ip_address, out);
    out << "\n";
  }

  // member: remote_ip_address
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "remote_ip_address: ";
    rosidl_generator_traits::value_to_yaml(msg.remote_ip_address, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const MocapNetwork & msg, bool use_flow_style = false)
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
  const genie_msgs::msg::MocapNetwork & msg,
  std::ostream & out, size_t indentation = 0)
{
  genie_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use genie_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const genie_msgs::msg::MocapNetwork & msg)
{
  return genie_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<genie_msgs::msg::MocapNetwork>()
{
  return "genie_msgs::msg::MocapNetwork";
}

template<>
inline const char * name<genie_msgs::msg::MocapNetwork>()
{
  return "genie_msgs/msg/MocapNetwork";
}

template<>
struct has_fixed_size<genie_msgs::msg::MocapNetwork>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<genie_msgs::msg::MocapNetwork>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<genie_msgs::msg::MocapNetwork>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // GENIE_MSGS__MSG__DETAIL__MOCAP_NETWORK__TRAITS_HPP_
