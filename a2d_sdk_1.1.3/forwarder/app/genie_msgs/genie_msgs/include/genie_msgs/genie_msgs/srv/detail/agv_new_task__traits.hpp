// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from genie_msgs:srv/AGVNewTask.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__AGV_NEW_TASK__TRAITS_HPP_
#define GENIE_MSGS__SRV__DETAIL__AGV_NEW_TASK__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "genie_msgs/srv/detail/agv_new_task__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"
// Member 'target_station_list'
#include "genie_msgs/msg/detail/target_station__traits.hpp"

namespace genie_msgs
{

namespace srv
{

inline void to_flow_style_yaml(
  const AGVNewTask_Request & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: task_reqid
  {
    out << "task_reqid: ";
    rosidl_generator_traits::value_to_yaml(msg.task_reqid, out);
    out << ", ";
  }

  // member: map_id
  {
    out << "map_id: ";
    rosidl_generator_traits::value_to_yaml(msg.map_id, out);
    out << ", ";
  }

  // member: target_station_list
  {
    if (msg.target_station_list.size() == 0) {
      out << "target_station_list: []";
    } else {
      out << "target_station_list: [";
      size_t pending_items = msg.target_station_list.size();
      for (auto item : msg.target_station_list) {
        to_flow_style_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: is_loop
  {
    out << "is_loop: ";
    rosidl_generator_traits::value_to_yaml(msg.is_loop, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const AGVNewTask_Request & msg,
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

  // member: task_reqid
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "task_reqid: ";
    rosidl_generator_traits::value_to_yaml(msg.task_reqid, out);
    out << "\n";
  }

  // member: map_id
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "map_id: ";
    rosidl_generator_traits::value_to_yaml(msg.map_id, out);
    out << "\n";
  }

  // member: target_station_list
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.target_station_list.size() == 0) {
      out << "target_station_list: []\n";
    } else {
      out << "target_station_list:\n";
      for (auto item : msg.target_station_list) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "-\n";
        to_block_style_yaml(item, out, indentation + 2);
      }
    }
  }

  // member: is_loop
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "is_loop: ";
    rosidl_generator_traits::value_to_yaml(msg.is_loop, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const AGVNewTask_Request & msg, bool use_flow_style = false)
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
  const genie_msgs::srv::AGVNewTask_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  genie_msgs::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use genie_msgs::srv::to_yaml() instead")]]
inline std::string to_yaml(const genie_msgs::srv::AGVNewTask_Request & msg)
{
  return genie_msgs::srv::to_yaml(msg);
}

template<>
inline const char * data_type<genie_msgs::srv::AGVNewTask_Request>()
{
  return "genie_msgs::srv::AGVNewTask_Request";
}

template<>
inline const char * name<genie_msgs::srv::AGVNewTask_Request>()
{
  return "genie_msgs/srv/AGVNewTask_Request";
}

template<>
struct has_fixed_size<genie_msgs::srv::AGVNewTask_Request>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<genie_msgs::srv::AGVNewTask_Request>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<genie_msgs::srv::AGVNewTask_Request>
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
  const AGVNewTask_Response & msg,
  std::ostream & out)
{
  out << "{";
  // member: res_header
  {
    out << "res_header: ";
    to_flow_style_yaml(msg.res_header, out);
    out << ", ";
  }

  // member: req_result
  {
    out << "req_result: ";
    rosidl_generator_traits::value_to_yaml(msg.req_result, out);
    out << ", ";
  }

  // member: ret_code
  {
    out << "ret_code: ";
    rosidl_generator_traits::value_to_yaml(msg.ret_code, out);
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
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const AGVNewTask_Response & msg,
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

  // member: req_result
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "req_result: ";
    rosidl_generator_traits::value_to_yaml(msg.req_result, out);
    out << "\n";
  }

  // member: ret_code
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "ret_code: ";
    rosidl_generator_traits::value_to_yaml(msg.ret_code, out);
    out << "\n";
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
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const AGVNewTask_Response & msg, bool use_flow_style = false)
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
  const genie_msgs::srv::AGVNewTask_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  genie_msgs::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use genie_msgs::srv::to_yaml() instead")]]
inline std::string to_yaml(const genie_msgs::srv::AGVNewTask_Response & msg)
{
  return genie_msgs::srv::to_yaml(msg);
}

template<>
inline const char * data_type<genie_msgs::srv::AGVNewTask_Response>()
{
  return "genie_msgs::srv::AGVNewTask_Response";
}

template<>
inline const char * name<genie_msgs::srv::AGVNewTask_Response>()
{
  return "genie_msgs/srv/AGVNewTask_Response";
}

template<>
struct has_fixed_size<genie_msgs::srv::AGVNewTask_Response>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<genie_msgs::srv::AGVNewTask_Response>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<genie_msgs::srv::AGVNewTask_Response>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<genie_msgs::srv::AGVNewTask>()
{
  return "genie_msgs::srv::AGVNewTask";
}

template<>
inline const char * name<genie_msgs::srv::AGVNewTask>()
{
  return "genie_msgs/srv/AGVNewTask";
}

template<>
struct has_fixed_size<genie_msgs::srv::AGVNewTask>
  : std::integral_constant<
    bool,
    has_fixed_size<genie_msgs::srv::AGVNewTask_Request>::value &&
    has_fixed_size<genie_msgs::srv::AGVNewTask_Response>::value
  >
{
};

template<>
struct has_bounded_size<genie_msgs::srv::AGVNewTask>
  : std::integral_constant<
    bool,
    has_bounded_size<genie_msgs::srv::AGVNewTask_Request>::value &&
    has_bounded_size<genie_msgs::srv::AGVNewTask_Response>::value
  >
{
};

template<>
struct is_service<genie_msgs::srv::AGVNewTask>
  : std::true_type
{
};

template<>
struct is_service_request<genie_msgs::srv::AGVNewTask_Request>
  : std::true_type
{
};

template<>
struct is_service_response<genie_msgs::srv::AGVNewTask_Response>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits

#endif  // GENIE_MSGS__SRV__DETAIL__AGV_NEW_TASK__TRAITS_HPP_
