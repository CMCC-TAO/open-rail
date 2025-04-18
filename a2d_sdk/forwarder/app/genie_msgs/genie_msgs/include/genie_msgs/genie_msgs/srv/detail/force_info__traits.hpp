// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from genie_msgs:srv/ForceInfo.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__FORCE_INFO__TRAITS_HPP_
#define GENIE_MSGS__SRV__DETAIL__FORCE_INFO__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "genie_msgs/srv/detail/force_info__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"

namespace genie_msgs
{

namespace srv
{

inline void to_flow_style_yaml(
  const ForceInfo_Request & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: force_id
  {
    out << "force_id: ";
    rosidl_generator_traits::value_to_yaml(msg.force_id, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const ForceInfo_Request & msg,
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

  // member: force_id
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "force_id: ";
    rosidl_generator_traits::value_to_yaml(msg.force_id, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const ForceInfo_Request & msg, bool use_flow_style = false)
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
  const genie_msgs::srv::ForceInfo_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  genie_msgs::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use genie_msgs::srv::to_yaml() instead")]]
inline std::string to_yaml(const genie_msgs::srv::ForceInfo_Request & msg)
{
  return genie_msgs::srv::to_yaml(msg);
}

template<>
inline const char * data_type<genie_msgs::srv::ForceInfo_Request>()
{
  return "genie_msgs::srv::ForceInfo_Request";
}

template<>
inline const char * name<genie_msgs::srv::ForceInfo_Request>()
{
  return "genie_msgs/srv/ForceInfo_Request";
}

template<>
struct has_fixed_size<genie_msgs::srv::ForceInfo_Request>
  : std::integral_constant<bool, has_fixed_size<std_msgs::msg::Header>::value> {};

template<>
struct has_bounded_size<genie_msgs::srv::ForceInfo_Request>
  : std::integral_constant<bool, has_bounded_size<std_msgs::msg::Header>::value> {};

template<>
struct is_message<genie_msgs::srv::ForceInfo_Request>
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
  const ForceInfo_Response & msg,
  std::ostream & out)
{
  out << "{";
  // member: res_header
  {
    out << "res_header: ";
    to_flow_style_yaml(msg.res_header, out);
    out << ", ";
  }

  // member: exec_result
  {
    out << "exec_result: ";
    rosidl_generator_traits::value_to_yaml(msg.exec_result, out);
    out << ", ";
  }

  // member: work_zero_force_data
  {
    if (msg.work_zero_force_data.size() == 0) {
      out << "work_zero_force_data: []";
    } else {
      out << "work_zero_force_data: [";
      size_t pending_items = msg.work_zero_force_data.size();
      for (auto item : msg.work_zero_force_data) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: tool_zero_force_data
  {
    if (msg.tool_zero_force_data.size() == 0) {
      out << "tool_zero_force_data: []";
    } else {
      out << "tool_zero_force_data: [";
      size_t pending_items = msg.tool_zero_force_data.size();
      for (auto item : msg.tool_zero_force_data) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: zero_force_data
  {
    if (msg.zero_force_data.size() == 0) {
      out << "zero_force_data: []";
    } else {
      out << "zero_force_data: [";
      size_t pending_items = msg.zero_force_data.size();
      for (auto item : msg.zero_force_data) {
        rosidl_generator_traits::value_to_yaml(item, out);
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
  const ForceInfo_Response & msg,
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

  // member: exec_result
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "exec_result: ";
    rosidl_generator_traits::value_to_yaml(msg.exec_result, out);
    out << "\n";
  }

  // member: work_zero_force_data
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.work_zero_force_data.size() == 0) {
      out << "work_zero_force_data: []\n";
    } else {
      out << "work_zero_force_data:\n";
      for (auto item : msg.work_zero_force_data) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }

  // member: tool_zero_force_data
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.tool_zero_force_data.size() == 0) {
      out << "tool_zero_force_data: []\n";
    } else {
      out << "tool_zero_force_data:\n";
      for (auto item : msg.tool_zero_force_data) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }

  // member: zero_force_data
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.zero_force_data.size() == 0) {
      out << "zero_force_data: []\n";
    } else {
      out << "zero_force_data:\n";
      for (auto item : msg.zero_force_data) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const ForceInfo_Response & msg, bool use_flow_style = false)
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
  const genie_msgs::srv::ForceInfo_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  genie_msgs::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use genie_msgs::srv::to_yaml() instead")]]
inline std::string to_yaml(const genie_msgs::srv::ForceInfo_Response & msg)
{
  return genie_msgs::srv::to_yaml(msg);
}

template<>
inline const char * data_type<genie_msgs::srv::ForceInfo_Response>()
{
  return "genie_msgs::srv::ForceInfo_Response";
}

template<>
inline const char * name<genie_msgs::srv::ForceInfo_Response>()
{
  return "genie_msgs/srv/ForceInfo_Response";
}

template<>
struct has_fixed_size<genie_msgs::srv::ForceInfo_Response>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<genie_msgs::srv::ForceInfo_Response>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<genie_msgs::srv::ForceInfo_Response>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<genie_msgs::srv::ForceInfo>()
{
  return "genie_msgs::srv::ForceInfo";
}

template<>
inline const char * name<genie_msgs::srv::ForceInfo>()
{
  return "genie_msgs/srv/ForceInfo";
}

template<>
struct has_fixed_size<genie_msgs::srv::ForceInfo>
  : std::integral_constant<
    bool,
    has_fixed_size<genie_msgs::srv::ForceInfo_Request>::value &&
    has_fixed_size<genie_msgs::srv::ForceInfo_Response>::value
  >
{
};

template<>
struct has_bounded_size<genie_msgs::srv::ForceInfo>
  : std::integral_constant<
    bool,
    has_bounded_size<genie_msgs::srv::ForceInfo_Request>::value &&
    has_bounded_size<genie_msgs::srv::ForceInfo_Response>::value
  >
{
};

template<>
struct is_service<genie_msgs::srv::ForceInfo>
  : std::true_type
{
};

template<>
struct is_service_request<genie_msgs::srv::ForceInfo_Request>
  : std::true_type
{
};

template<>
struct is_service_response<genie_msgs::srv::ForceInfo_Response>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits

#endif  // GENIE_MSGS__SRV__DETAIL__FORCE_INFO__TRAITS_HPP_
