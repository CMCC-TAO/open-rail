// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from genie_msgs:srv/FeatGetCtrlMode.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__FEAT_GET_CTRL_MODE__TRAITS_HPP_
#define GENIE_MSGS__SRV__DETAIL__FEAT_GET_CTRL_MODE__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "genie_msgs/srv/detail/feat_get_ctrl_mode__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"

namespace genie_msgs
{

namespace srv
{

inline void to_flow_style_yaml(
  const FeatGetCtrlMode_Request & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const FeatGetCtrlMode_Request & msg,
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
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const FeatGetCtrlMode_Request & msg, bool use_flow_style = false)
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
  const genie_msgs::srv::FeatGetCtrlMode_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  genie_msgs::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use genie_msgs::srv::to_yaml() instead")]]
inline std::string to_yaml(const genie_msgs::srv::FeatGetCtrlMode_Request & msg)
{
  return genie_msgs::srv::to_yaml(msg);
}

template<>
inline const char * data_type<genie_msgs::srv::FeatGetCtrlMode_Request>()
{
  return "genie_msgs::srv::FeatGetCtrlMode_Request";
}

template<>
inline const char * name<genie_msgs::srv::FeatGetCtrlMode_Request>()
{
  return "genie_msgs/srv/FeatGetCtrlMode_Request";
}

template<>
struct has_fixed_size<genie_msgs::srv::FeatGetCtrlMode_Request>
  : std::integral_constant<bool, has_fixed_size<std_msgs::msg::Header>::value> {};

template<>
struct has_bounded_size<genie_msgs::srv::FeatGetCtrlMode_Request>
  : std::integral_constant<bool, has_bounded_size<std_msgs::msg::Header>::value> {};

template<>
struct is_message<genie_msgs::srv::FeatGetCtrlMode_Request>
  : std::true_type {};

}  // namespace rosidl_generator_traits

// Include directives for member types
// Member 'res_header'
// already included above
// #include "std_msgs/msg/detail/header__traits.hpp"

namespace genie_msgs
{

namespace srv
{

inline void to_flow_style_yaml(
  const FeatGetCtrlMode_Response & msg,
  std::ostream & out)
{
  out << "{";
  // member: res_header
  {
    out << "res_header: ";
    to_flow_style_yaml(msg.res_header, out);
    out << ", ";
  }

  // member: online
  {
    out << "online: ";
    rosidl_generator_traits::value_to_yaml(msg.online, out);
    out << ", ";
  }

  // member: remote_mode
  {
    out << "remote_mode: ";
    rosidl_generator_traits::value_to_yaml(msg.remote_mode, out);
    out << ", ";
  }

  // member: ctrl_mode
  {
    out << "ctrl_mode: ";
    rosidl_generator_traits::value_to_yaml(msg.ctrl_mode, out);
    out << ", ";
  }

  // member: exec_result
  {
    out << "exec_result: ";
    rosidl_generator_traits::value_to_yaml(msg.exec_result, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const FeatGetCtrlMode_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: res_header
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "res_header:\n";
    to_block_style_yaml(msg.res_header, out, indentation + 2);
  }

  // member: online
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "online: ";
    rosidl_generator_traits::value_to_yaml(msg.online, out);
    out << "\n";
  }

  // member: remote_mode
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "remote_mode: ";
    rosidl_generator_traits::value_to_yaml(msg.remote_mode, out);
    out << "\n";
  }

  // member: ctrl_mode
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "ctrl_mode: ";
    rosidl_generator_traits::value_to_yaml(msg.ctrl_mode, out);
    out << "\n";
  }

  // member: exec_result
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "exec_result: ";
    rosidl_generator_traits::value_to_yaml(msg.exec_result, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const FeatGetCtrlMode_Response & msg, bool use_flow_style = false)
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
  const genie_msgs::srv::FeatGetCtrlMode_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  genie_msgs::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use genie_msgs::srv::to_yaml() instead")]]
inline std::string to_yaml(const genie_msgs::srv::FeatGetCtrlMode_Response & msg)
{
  return genie_msgs::srv::to_yaml(msg);
}

template<>
inline const char * data_type<genie_msgs::srv::FeatGetCtrlMode_Response>()
{
  return "genie_msgs::srv::FeatGetCtrlMode_Response";
}

template<>
inline const char * name<genie_msgs::srv::FeatGetCtrlMode_Response>()
{
  return "genie_msgs/srv/FeatGetCtrlMode_Response";
}

template<>
struct has_fixed_size<genie_msgs::srv::FeatGetCtrlMode_Response>
  : std::integral_constant<bool, has_fixed_size<std_msgs::msg::Header>::value> {};

template<>
struct has_bounded_size<genie_msgs::srv::FeatGetCtrlMode_Response>
  : std::integral_constant<bool, has_bounded_size<std_msgs::msg::Header>::value> {};

template<>
struct is_message<genie_msgs::srv::FeatGetCtrlMode_Response>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<genie_msgs::srv::FeatGetCtrlMode>()
{
  return "genie_msgs::srv::FeatGetCtrlMode";
}

template<>
inline const char * name<genie_msgs::srv::FeatGetCtrlMode>()
{
  return "genie_msgs/srv/FeatGetCtrlMode";
}

template<>
struct has_fixed_size<genie_msgs::srv::FeatGetCtrlMode>
  : std::integral_constant<
    bool,
    has_fixed_size<genie_msgs::srv::FeatGetCtrlMode_Request>::value &&
    has_fixed_size<genie_msgs::srv::FeatGetCtrlMode_Response>::value
  >
{
};

template<>
struct has_bounded_size<genie_msgs::srv::FeatGetCtrlMode>
  : std::integral_constant<
    bool,
    has_bounded_size<genie_msgs::srv::FeatGetCtrlMode_Request>::value &&
    has_bounded_size<genie_msgs::srv::FeatGetCtrlMode_Response>::value
  >
{
};

template<>
struct is_service<genie_msgs::srv::FeatGetCtrlMode>
  : std::true_type
{
};

template<>
struct is_service_request<genie_msgs::srv::FeatGetCtrlMode_Request>
  : std::true_type
{
};

template<>
struct is_service_response<genie_msgs::srv::FeatGetCtrlMode_Response>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits

#endif  // GENIE_MSGS__SRV__DETAIL__FEAT_GET_CTRL_MODE__TRAITS_HPP_
