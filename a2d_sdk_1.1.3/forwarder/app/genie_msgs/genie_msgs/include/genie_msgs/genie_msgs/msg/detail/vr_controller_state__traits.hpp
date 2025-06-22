// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from genie_msgs:msg/VRControllerState.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__VR_CONTROLLER_STATE__TRAITS_HPP_
#define GENIE_MSGS__MSG__DETAIL__VR_CONTROLLER_STATE__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "genie_msgs/msg/detail/vr_controller_state__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'position'
#include "geometry_msgs/msg/detail/vector3__traits.hpp"
// Member 'orientation'
#include "geometry_msgs/msg/detail/quaternion__traits.hpp"

namespace genie_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const VRControllerState & msg,
  std::ostream & out)
{
  out << "{";
  // member: name
  {
    out << "name: ";
    rosidl_generator_traits::value_to_yaml(msg.name, out);
    out << ", ";
  }

  // member: id
  {
    out << "id: ";
    rosidl_generator_traits::value_to_yaml(msg.id, out);
    out << ", ";
  }

  // member: key_one
  {
    out << "key_one: ";
    rosidl_generator_traits::value_to_yaml(msg.key_one, out);
    out << ", ";
  }

  // member: key_two
  {
    out << "key_two: ";
    rosidl_generator_traits::value_to_yaml(msg.key_two, out);
    out << ", ";
  }

  // member: hand_trig
  {
    out << "hand_trig: ";
    rosidl_generator_traits::value_to_yaml(msg.hand_trig, out);
    out << ", ";
  }

  // member: index_trig
  {
    out << "index_trig: ";
    rosidl_generator_traits::value_to_yaml(msg.index_trig, out);
    out << ", ";
  }

  // member: axis_x
  {
    out << "axis_x: ";
    rosidl_generator_traits::value_to_yaml(msg.axis_x, out);
    out << ", ";
  }

  // member: axis_y
  {
    out << "axis_y: ";
    rosidl_generator_traits::value_to_yaml(msg.axis_y, out);
    out << ", ";
  }

  // member: axis_click
  {
    out << "axis_click: ";
    rosidl_generator_traits::value_to_yaml(msg.axis_click, out);
    out << ", ";
  }

  // member: position
  {
    out << "position: ";
    to_flow_style_yaml(msg.position, out);
    out << ", ";
  }

  // member: orientation
  {
    out << "orientation: ";
    to_flow_style_yaml(msg.orientation, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const VRControllerState & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: name
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "name: ";
    rosidl_generator_traits::value_to_yaml(msg.name, out);
    out << "\n";
  }

  // member: id
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "id: ";
    rosidl_generator_traits::value_to_yaml(msg.id, out);
    out << "\n";
  }

  // member: key_one
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "key_one: ";
    rosidl_generator_traits::value_to_yaml(msg.key_one, out);
    out << "\n";
  }

  // member: key_two
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "key_two: ";
    rosidl_generator_traits::value_to_yaml(msg.key_two, out);
    out << "\n";
  }

  // member: hand_trig
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "hand_trig: ";
    rosidl_generator_traits::value_to_yaml(msg.hand_trig, out);
    out << "\n";
  }

  // member: index_trig
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "index_trig: ";
    rosidl_generator_traits::value_to_yaml(msg.index_trig, out);
    out << "\n";
  }

  // member: axis_x
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "axis_x: ";
    rosidl_generator_traits::value_to_yaml(msg.axis_x, out);
    out << "\n";
  }

  // member: axis_y
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "axis_y: ";
    rosidl_generator_traits::value_to_yaml(msg.axis_y, out);
    out << "\n";
  }

  // member: axis_click
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "axis_click: ";
    rosidl_generator_traits::value_to_yaml(msg.axis_click, out);
    out << "\n";
  }

  // member: position
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "position:\n";
    to_block_style_yaml(msg.position, out, indentation + 2);
  }

  // member: orientation
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "orientation:\n";
    to_block_style_yaml(msg.orientation, out, indentation + 2);
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const VRControllerState & msg, bool use_flow_style = false)
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
  const genie_msgs::msg::VRControllerState & msg,
  std::ostream & out, size_t indentation = 0)
{
  genie_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use genie_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const genie_msgs::msg::VRControllerState & msg)
{
  return genie_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<genie_msgs::msg::VRControllerState>()
{
  return "genie_msgs::msg::VRControllerState";
}

template<>
inline const char * name<genie_msgs::msg::VRControllerState>()
{
  return "genie_msgs/msg/VRControllerState";
}

template<>
struct has_fixed_size<genie_msgs::msg::VRControllerState>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<genie_msgs::msg::VRControllerState>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<genie_msgs::msg::VRControllerState>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // GENIE_MSGS__MSG__DETAIL__VR_CONTROLLER_STATE__TRAITS_HPP_
