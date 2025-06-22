// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from genie_msgs:srv/NoitomSetFreq.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__NOITOM_SET_FREQ__TRAITS_HPP_
#define GENIE_MSGS__SRV__DETAIL__NOITOM_SET_FREQ__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "genie_msgs/srv/detail/noitom_set_freq__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace genie_msgs
{

namespace srv
{

inline void to_flow_style_yaml(
  const NoitomSetFreq_Request & msg,
  std::ostream & out)
{
  out << "{";
  // member: frequency
  {
    out << "frequency: ";
    rosidl_generator_traits::value_to_yaml(msg.frequency, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const NoitomSetFreq_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: frequency
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "frequency: ";
    rosidl_generator_traits::value_to_yaml(msg.frequency, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const NoitomSetFreq_Request & msg, bool use_flow_style = false)
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
  const genie_msgs::srv::NoitomSetFreq_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  genie_msgs::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use genie_msgs::srv::to_yaml() instead")]]
inline std::string to_yaml(const genie_msgs::srv::NoitomSetFreq_Request & msg)
{
  return genie_msgs::srv::to_yaml(msg);
}

template<>
inline const char * data_type<genie_msgs::srv::NoitomSetFreq_Request>()
{
  return "genie_msgs::srv::NoitomSetFreq_Request";
}

template<>
inline const char * name<genie_msgs::srv::NoitomSetFreq_Request>()
{
  return "genie_msgs/srv/NoitomSetFreq_Request";
}

template<>
struct has_fixed_size<genie_msgs::srv::NoitomSetFreq_Request>
  : std::integral_constant<bool, true> {};

template<>
struct has_bounded_size<genie_msgs::srv::NoitomSetFreq_Request>
  : std::integral_constant<bool, true> {};

template<>
struct is_message<genie_msgs::srv::NoitomSetFreq_Request>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace genie_msgs
{

namespace srv
{

inline void to_flow_style_yaml(
  const NoitomSetFreq_Response & msg,
  std::ostream & out)
{
  out << "{";
  // member: success
  {
    out << "success: ";
    rosidl_generator_traits::value_to_yaml(msg.success, out);
    out << ", ";
  }

  // member: current_frequency
  {
    out << "current_frequency: ";
    rosidl_generator_traits::value_to_yaml(msg.current_frequency, out);
    out << ", ";
  }

  // member: message
  {
    out << "message: ";
    rosidl_generator_traits::value_to_yaml(msg.message, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const NoitomSetFreq_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: success
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "success: ";
    rosidl_generator_traits::value_to_yaml(msg.success, out);
    out << "\n";
  }

  // member: current_frequency
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "current_frequency: ";
    rosidl_generator_traits::value_to_yaml(msg.current_frequency, out);
    out << "\n";
  }

  // member: message
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "message: ";
    rosidl_generator_traits::value_to_yaml(msg.message, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const NoitomSetFreq_Response & msg, bool use_flow_style = false)
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
  const genie_msgs::srv::NoitomSetFreq_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  genie_msgs::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use genie_msgs::srv::to_yaml() instead")]]
inline std::string to_yaml(const genie_msgs::srv::NoitomSetFreq_Response & msg)
{
  return genie_msgs::srv::to_yaml(msg);
}

template<>
inline const char * data_type<genie_msgs::srv::NoitomSetFreq_Response>()
{
  return "genie_msgs::srv::NoitomSetFreq_Response";
}

template<>
inline const char * name<genie_msgs::srv::NoitomSetFreq_Response>()
{
  return "genie_msgs/srv/NoitomSetFreq_Response";
}

template<>
struct has_fixed_size<genie_msgs::srv::NoitomSetFreq_Response>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<genie_msgs::srv::NoitomSetFreq_Response>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<genie_msgs::srv::NoitomSetFreq_Response>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<genie_msgs::srv::NoitomSetFreq>()
{
  return "genie_msgs::srv::NoitomSetFreq";
}

template<>
inline const char * name<genie_msgs::srv::NoitomSetFreq>()
{
  return "genie_msgs/srv/NoitomSetFreq";
}

template<>
struct has_fixed_size<genie_msgs::srv::NoitomSetFreq>
  : std::integral_constant<
    bool,
    has_fixed_size<genie_msgs::srv::NoitomSetFreq_Request>::value &&
    has_fixed_size<genie_msgs::srv::NoitomSetFreq_Response>::value
  >
{
};

template<>
struct has_bounded_size<genie_msgs::srv::NoitomSetFreq>
  : std::integral_constant<
    bool,
    has_bounded_size<genie_msgs::srv::NoitomSetFreq_Request>::value &&
    has_bounded_size<genie_msgs::srv::NoitomSetFreq_Response>::value
  >
{
};

template<>
struct is_service<genie_msgs::srv::NoitomSetFreq>
  : std::true_type
{
};

template<>
struct is_service_request<genie_msgs::srv::NoitomSetFreq_Request>
  : std::true_type
{
};

template<>
struct is_service_response<genie_msgs::srv::NoitomSetFreq_Response>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits

#endif  // GENIE_MSGS__SRV__DETAIL__NOITOM_SET_FREQ__TRAITS_HPP_
