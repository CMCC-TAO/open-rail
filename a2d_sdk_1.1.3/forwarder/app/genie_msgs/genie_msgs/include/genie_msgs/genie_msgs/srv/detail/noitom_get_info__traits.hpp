// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from genie_msgs:srv/NoitomGetInfo.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__NOITOM_GET_INFO__TRAITS_HPP_
#define GENIE_MSGS__SRV__DETAIL__NOITOM_GET_INFO__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "genie_msgs/srv/detail/noitom_get_info__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace genie_msgs
{

namespace srv
{

inline void to_flow_style_yaml(
  const NoitomGetInfo_Request & msg,
  std::ostream & out)
{
  (void)msg;
  out << "null";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const NoitomGetInfo_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  (void)msg;
  (void)indentation;
  out << "null\n";
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const NoitomGetInfo_Request & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace srv

}  // namespace genie_msgs

namespace rosidl_generator_traits
{

[[deprecated("use genie_msgs::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const genie_msgs::srv::NoitomGetInfo_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  genie_msgs::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use genie_msgs::srv::to_yaml() instead")]]
inline std::string to_yaml(const genie_msgs::srv::NoitomGetInfo_Request & msg)
{
  return genie_msgs::srv::to_yaml(msg);
}

template<>
inline const char * data_type<genie_msgs::srv::NoitomGetInfo_Request>()
{
  return "genie_msgs::srv::NoitomGetInfo_Request";
}

template<>
inline const char * name<genie_msgs::srv::NoitomGetInfo_Request>()
{
  return "genie_msgs/srv/NoitomGetInfo_Request";
}

template<>
struct has_fixed_size<genie_msgs::srv::NoitomGetInfo_Request>
  : std::integral_constant<bool, true> {};

template<>
struct has_bounded_size<genie_msgs::srv::NoitomGetInfo_Request>
  : std::integral_constant<bool, true> {};

template<>
struct is_message<genie_msgs::srv::NoitomGetInfo_Request>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace genie_msgs
{

namespace srv
{

inline void to_flow_style_yaml(
  const NoitomGetInfo_Response & msg,
  std::ostream & out)
{
  out << "{";
  // member: device_sn
  {
    out << "device_sn: ";
    rosidl_generator_traits::value_to_yaml(msg.device_sn, out);
    out << ", ";
  }

  // member: software_version
  {
    out << "software_version: ";
    rosidl_generator_traits::value_to_yaml(msg.software_version, out);
    out << ", ";
  }

  // member: hardware_date
  {
    out << "hardware_date: ";
    rosidl_generator_traits::value_to_yaml(msg.hardware_date, out);
    out << ", ";
  }

  // member: default_ip
  {
    out << "default_ip: ";
    rosidl_generator_traits::value_to_yaml(msg.default_ip, out);
    out << ", ";
  }

  // member: default_port
  {
    out << "default_port: ";
    rosidl_generator_traits::value_to_yaml(msg.default_port, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const NoitomGetInfo_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: device_sn
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "device_sn: ";
    rosidl_generator_traits::value_to_yaml(msg.device_sn, out);
    out << "\n";
  }

  // member: software_version
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "software_version: ";
    rosidl_generator_traits::value_to_yaml(msg.software_version, out);
    out << "\n";
  }

  // member: hardware_date
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "hardware_date: ";
    rosidl_generator_traits::value_to_yaml(msg.hardware_date, out);
    out << "\n";
  }

  // member: default_ip
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "default_ip: ";
    rosidl_generator_traits::value_to_yaml(msg.default_ip, out);
    out << "\n";
  }

  // member: default_port
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "default_port: ";
    rosidl_generator_traits::value_to_yaml(msg.default_port, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const NoitomGetInfo_Response & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace srv

}  // namespace genie_msgs

namespace rosidl_generator_traits
{

[[deprecated("use genie_msgs::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const genie_msgs::srv::NoitomGetInfo_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  genie_msgs::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use genie_msgs::srv::to_yaml() instead")]]
inline std::string to_yaml(const genie_msgs::srv::NoitomGetInfo_Response & msg)
{
  return genie_msgs::srv::to_yaml(msg);
}

template<>
inline const char * data_type<genie_msgs::srv::NoitomGetInfo_Response>()
{
  return "genie_msgs::srv::NoitomGetInfo_Response";
}

template<>
inline const char * name<genie_msgs::srv::NoitomGetInfo_Response>()
{
  return "genie_msgs/srv/NoitomGetInfo_Response";
}

template<>
struct has_fixed_size<genie_msgs::srv::NoitomGetInfo_Response>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<genie_msgs::srv::NoitomGetInfo_Response>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<genie_msgs::srv::NoitomGetInfo_Response>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<genie_msgs::srv::NoitomGetInfo>()
{
  return "genie_msgs::srv::NoitomGetInfo";
}

template<>
inline const char * name<genie_msgs::srv::NoitomGetInfo>()
{
  return "genie_msgs/srv/NoitomGetInfo";
}

template<>
struct has_fixed_size<genie_msgs::srv::NoitomGetInfo>
  : std::integral_constant<
    bool,
    has_fixed_size<genie_msgs::srv::NoitomGetInfo_Request>::value &&
    has_fixed_size<genie_msgs::srv::NoitomGetInfo_Response>::value
  >
{
};

template<>
struct has_bounded_size<genie_msgs::srv::NoitomGetInfo>
  : std::integral_constant<
    bool,
    has_bounded_size<genie_msgs::srv::NoitomGetInfo_Request>::value &&
    has_bounded_size<genie_msgs::srv::NoitomGetInfo_Response>::value
  >
{
};

template<>
struct is_service<genie_msgs::srv::NoitomGetInfo>
  : std::true_type
{
};

template<>
struct is_service_request<genie_msgs::srv::NoitomGetInfo_Request>
  : std::true_type
{
};

template<>
struct is_service_response<genie_msgs::srv::NoitomGetInfo_Response>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits

#endif  // GENIE_MSGS__SRV__DETAIL__NOITOM_GET_INFO__TRAITS_HPP_
