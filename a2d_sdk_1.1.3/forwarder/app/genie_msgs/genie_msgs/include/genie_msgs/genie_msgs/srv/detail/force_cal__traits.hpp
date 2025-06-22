// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from genie_msgs:srv/ForceCal.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__FORCE_CAL__TRAITS_HPP_
#define GENIE_MSGS__SRV__DETAIL__FORCE_CAL__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "genie_msgs/srv/detail/force_cal__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"

namespace genie_msgs
{

namespace srv
{

inline void to_flow_style_yaml(
  const ForceCal_Request & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: cal_cmd
  {
    out << "cal_cmd: ";
    rosidl_generator_traits::value_to_yaml(msg.cal_cmd, out);
    out << ", ";
  }

  // member: force_id
  {
    out << "force_id: ";
    rosidl_generator_traits::value_to_yaml(msg.force_id, out);
    out << ", ";
  }

  // member: count
  {
    out << "count: ";
    rosidl_generator_traits::value_to_yaml(msg.count, out);
    out << ", ";
  }

  // member: joint
  {
    if (msg.joint.size() == 0) {
      out << "joint: []";
    } else {
      out << "joint: [";
      size_t pending_items = msg.joint.size();
      for (auto item : msg.joint) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: block
  {
    out << "block: ";
    rosidl_generator_traits::value_to_yaml(msg.block, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const ForceCal_Request & msg,
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

  // member: cal_cmd
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "cal_cmd: ";
    rosidl_generator_traits::value_to_yaml(msg.cal_cmd, out);
    out << "\n";
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

  // member: count
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "count: ";
    rosidl_generator_traits::value_to_yaml(msg.count, out);
    out << "\n";
  }

  // member: joint
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.joint.size() == 0) {
      out << "joint: []\n";
    } else {
      out << "joint:\n";
      for (auto item : msg.joint) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }

  // member: block
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "block: ";
    rosidl_generator_traits::value_to_yaml(msg.block, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const ForceCal_Request & msg, bool use_flow_style = false)
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
  const genie_msgs::srv::ForceCal_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  genie_msgs::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use genie_msgs::srv::to_yaml() instead")]]
inline std::string to_yaml(const genie_msgs::srv::ForceCal_Request & msg)
{
  return genie_msgs::srv::to_yaml(msg);
}

template<>
inline const char * data_type<genie_msgs::srv::ForceCal_Request>()
{
  return "genie_msgs::srv::ForceCal_Request";
}

template<>
inline const char * name<genie_msgs::srv::ForceCal_Request>()
{
  return "genie_msgs/srv/ForceCal_Request";
}

template<>
struct has_fixed_size<genie_msgs::srv::ForceCal_Request>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<genie_msgs::srv::ForceCal_Request>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<genie_msgs::srv::ForceCal_Request>
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
  const ForceCal_Response & msg,
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
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const ForceCal_Response & msg,
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
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const ForceCal_Response & msg, bool use_flow_style = false)
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
  const genie_msgs::srv::ForceCal_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  genie_msgs::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use genie_msgs::srv::to_yaml() instead")]]
inline std::string to_yaml(const genie_msgs::srv::ForceCal_Response & msg)
{
  return genie_msgs::srv::to_yaml(msg);
}

template<>
inline const char * data_type<genie_msgs::srv::ForceCal_Response>()
{
  return "genie_msgs::srv::ForceCal_Response";
}

template<>
inline const char * name<genie_msgs::srv::ForceCal_Response>()
{
  return "genie_msgs/srv/ForceCal_Response";
}

template<>
struct has_fixed_size<genie_msgs::srv::ForceCal_Response>
  : std::integral_constant<bool, has_fixed_size<std_msgs::msg::Header>::value> {};

template<>
struct has_bounded_size<genie_msgs::srv::ForceCal_Response>
  : std::integral_constant<bool, has_bounded_size<std_msgs::msg::Header>::value> {};

template<>
struct is_message<genie_msgs::srv::ForceCal_Response>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<genie_msgs::srv::ForceCal>()
{
  return "genie_msgs::srv::ForceCal";
}

template<>
inline const char * name<genie_msgs::srv::ForceCal>()
{
  return "genie_msgs/srv/ForceCal";
}

template<>
struct has_fixed_size<genie_msgs::srv::ForceCal>
  : std::integral_constant<
    bool,
    has_fixed_size<genie_msgs::srv::ForceCal_Request>::value &&
    has_fixed_size<genie_msgs::srv::ForceCal_Response>::value
  >
{
};

template<>
struct has_bounded_size<genie_msgs::srv::ForceCal>
  : std::integral_constant<
    bool,
    has_bounded_size<genie_msgs::srv::ForceCal_Request>::value &&
    has_bounded_size<genie_msgs::srv::ForceCal_Response>::value
  >
{
};

template<>
struct is_service<genie_msgs::srv::ForceCal>
  : std::true_type
{
};

template<>
struct is_service_request<genie_msgs::srv::ForceCal_Request>
  : std::true_type
{
};

template<>
struct is_service_response<genie_msgs::srv::ForceCal_Response>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits

#endif  // GENIE_MSGS__SRV__DETAIL__FORCE_CAL__TRAITS_HPP_
