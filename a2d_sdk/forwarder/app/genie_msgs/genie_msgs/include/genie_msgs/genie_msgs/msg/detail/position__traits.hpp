// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from genie_msgs:msg/Position.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__POSITION__TRAITS_HPP_
#define GENIE_MSGS__MSG__DETAIL__POSITION__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "genie_msgs/msg/detail/position__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"
// Member 'motor_states'
#include "genie_msgs/msg/detail/motor_state__traits.hpp"
// Member 'agv_task_state'
#include "genie_msgs/msg/detail/agv_task_state__traits.hpp"

namespace genie_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const Position & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: agv_status
  {
    out << "agv_status: ";
    rosidl_generator_traits::value_to_yaml(msg.agv_status, out);
    out << ", ";
  }

  // member: position_conf
  {
    out << "position_conf: ";
    rosidl_generator_traits::value_to_yaml(msg.position_conf, out);
    out << ", ";
  }

  // member: agv_pos_x
  {
    out << "agv_pos_x: ";
    rosidl_generator_traits::value_to_yaml(msg.agv_pos_x, out);
    out << ", ";
  }

  // member: agv_pos_y
  {
    out << "agv_pos_y: ";
    rosidl_generator_traits::value_to_yaml(msg.agv_pos_y, out);
    out << ", ";
  }

  // member: agv_pos_z
  {
    out << "agv_pos_z: ";
    rosidl_generator_traits::value_to_yaml(msg.agv_pos_z, out);
    out << ", ";
  }

  // member: agv_angle
  {
    out << "agv_angle: ";
    rosidl_generator_traits::value_to_yaml(msg.agv_angle, out);
    out << ", ";
  }

  // member: odom_x
  {
    out << "odom_x: ";
    rosidl_generator_traits::value_to_yaml(msg.odom_x, out);
    out << ", ";
  }

  // member: odom_y
  {
    out << "odom_y: ";
    rosidl_generator_traits::value_to_yaml(msg.odom_y, out);
    out << ", ";
  }

  // member: odom_z
  {
    out << "odom_z: ";
    rosidl_generator_traits::value_to_yaml(msg.odom_z, out);
    out << ", ";
  }

  // member: odom_angle
  {
    out << "odom_angle: ";
    rosidl_generator_traits::value_to_yaml(msg.odom_angle, out);
    out << ", ";
  }

  // member: linear_speed
  {
    out << "linear_speed: ";
    rosidl_generator_traits::value_to_yaml(msg.linear_speed, out);
    out << ", ";
  }

  // member: angular_speed
  {
    out << "angular_speed: ";
    rosidl_generator_traits::value_to_yaml(msg.angular_speed, out);
    out << ", ";
  }

  // member: acc_x
  {
    out << "acc_x: ";
    rosidl_generator_traits::value_to_yaml(msg.acc_x, out);
    out << ", ";
  }

  // member: acc_y
  {
    out << "acc_y: ";
    rosidl_generator_traits::value_to_yaml(msg.acc_y, out);
    out << ", ";
  }

  // member: acc_z
  {
    out << "acc_z: ";
    rosidl_generator_traits::value_to_yaml(msg.acc_z, out);
    out << ", ";
  }

  // member: gyro_x
  {
    out << "gyro_x: ";
    rosidl_generator_traits::value_to_yaml(msg.gyro_x, out);
    out << ", ";
  }

  // member: gyro_y
  {
    out << "gyro_y: ";
    rosidl_generator_traits::value_to_yaml(msg.gyro_y, out);
    out << ", ";
  }

  // member: gyro_z
  {
    out << "gyro_z: ";
    rosidl_generator_traits::value_to_yaml(msg.gyro_z, out);
    out << ", ";
  }

  // member: roll
  {
    out << "roll: ";
    rosidl_generator_traits::value_to_yaml(msg.roll, out);
    out << ", ";
  }

  // member: pitch
  {
    out << "pitch: ";
    rosidl_generator_traits::value_to_yaml(msg.pitch, out);
    out << ", ";
  }

  // member: yaw
  {
    out << "yaw: ";
    rosidl_generator_traits::value_to_yaml(msg.yaw, out);
    out << ", ";
  }

  // member: motor_states
  {
    if (msg.motor_states.size() == 0) {
      out << "motor_states: []";
    } else {
      out << "motor_states: [";
      size_t pending_items = msg.motor_states.size();
      for (auto item : msg.motor_states) {
        to_flow_style_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: agv_task_state
  {
    out << "agv_task_state: ";
    to_flow_style_yaml(msg.agv_task_state, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const Position & msg,
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

  // member: agv_status
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "agv_status: ";
    rosidl_generator_traits::value_to_yaml(msg.agv_status, out);
    out << "\n";
  }

  // member: position_conf
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "position_conf: ";
    rosidl_generator_traits::value_to_yaml(msg.position_conf, out);
    out << "\n";
  }

  // member: agv_pos_x
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "agv_pos_x: ";
    rosidl_generator_traits::value_to_yaml(msg.agv_pos_x, out);
    out << "\n";
  }

  // member: agv_pos_y
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "agv_pos_y: ";
    rosidl_generator_traits::value_to_yaml(msg.agv_pos_y, out);
    out << "\n";
  }

  // member: agv_pos_z
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "agv_pos_z: ";
    rosidl_generator_traits::value_to_yaml(msg.agv_pos_z, out);
    out << "\n";
  }

  // member: agv_angle
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "agv_angle: ";
    rosidl_generator_traits::value_to_yaml(msg.agv_angle, out);
    out << "\n";
  }

  // member: odom_x
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "odom_x: ";
    rosidl_generator_traits::value_to_yaml(msg.odom_x, out);
    out << "\n";
  }

  // member: odom_y
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "odom_y: ";
    rosidl_generator_traits::value_to_yaml(msg.odom_y, out);
    out << "\n";
  }

  // member: odom_z
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "odom_z: ";
    rosidl_generator_traits::value_to_yaml(msg.odom_z, out);
    out << "\n";
  }

  // member: odom_angle
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "odom_angle: ";
    rosidl_generator_traits::value_to_yaml(msg.odom_angle, out);
    out << "\n";
  }

  // member: linear_speed
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "linear_speed: ";
    rosidl_generator_traits::value_to_yaml(msg.linear_speed, out);
    out << "\n";
  }

  // member: angular_speed
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "angular_speed: ";
    rosidl_generator_traits::value_to_yaml(msg.angular_speed, out);
    out << "\n";
  }

  // member: acc_x
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "acc_x: ";
    rosidl_generator_traits::value_to_yaml(msg.acc_x, out);
    out << "\n";
  }

  // member: acc_y
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "acc_y: ";
    rosidl_generator_traits::value_to_yaml(msg.acc_y, out);
    out << "\n";
  }

  // member: acc_z
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "acc_z: ";
    rosidl_generator_traits::value_to_yaml(msg.acc_z, out);
    out << "\n";
  }

  // member: gyro_x
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "gyro_x: ";
    rosidl_generator_traits::value_to_yaml(msg.gyro_x, out);
    out << "\n";
  }

  // member: gyro_y
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "gyro_y: ";
    rosidl_generator_traits::value_to_yaml(msg.gyro_y, out);
    out << "\n";
  }

  // member: gyro_z
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "gyro_z: ";
    rosidl_generator_traits::value_to_yaml(msg.gyro_z, out);
    out << "\n";
  }

  // member: roll
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "roll: ";
    rosidl_generator_traits::value_to_yaml(msg.roll, out);
    out << "\n";
  }

  // member: pitch
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "pitch: ";
    rosidl_generator_traits::value_to_yaml(msg.pitch, out);
    out << "\n";
  }

  // member: yaw
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "yaw: ";
    rosidl_generator_traits::value_to_yaml(msg.yaw, out);
    out << "\n";
  }

  // member: motor_states
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.motor_states.size() == 0) {
      out << "motor_states: []\n";
    } else {
      out << "motor_states:\n";
      for (auto item : msg.motor_states) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "-\n";
        to_block_style_yaml(item, out, indentation + 2);
      }
    }
  }

  // member: agv_task_state
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "agv_task_state:\n";
    to_block_style_yaml(msg.agv_task_state, out, indentation + 2);
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const Position & msg, bool use_flow_style = false)
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
  const genie_msgs::msg::Position & msg,
  std::ostream & out, size_t indentation = 0)
{
  genie_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use genie_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const genie_msgs::msg::Position & msg)
{
  return genie_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<genie_msgs::msg::Position>()
{
  return "genie_msgs::msg::Position";
}

template<>
inline const char * name<genie_msgs::msg::Position>()
{
  return "genie_msgs/msg/Position";
}

template<>
struct has_fixed_size<genie_msgs::msg::Position>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<genie_msgs::msg::Position>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<genie_msgs::msg::Position>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // GENIE_MSGS__MSG__DETAIL__POSITION__TRAITS_HPP_
