// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from genie_msgs:msg/ModelPredict.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__MODEL_PREDICT__TRAITS_HPP_
#define GENIE_MSGS__MSG__DETAIL__MODEL_PREDICT__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "genie_msgs/msg/detail/model_predict__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"
// Member 'target_poses'
#include "geometry_msgs/msg/detail/pose__traits.hpp"
// Member 'target_joint_states'
#include "sensor_msgs/msg/detail/joint_state__traits.hpp"

namespace genie_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const ModelPredict & msg,
  std::ostream & out)
{
  out << "{";
  // member: header
  {
    out << "header: ";
    to_flow_style_yaml(msg.header, out);
    out << ", ";
  }

  // member: body_joint_names
  {
    if (msg.body_joint_names.size() == 0) {
      out << "body_joint_names: []";
    } else {
      out << "body_joint_names: [";
      size_t pending_items = msg.body_joint_names.size();
      for (auto item : msg.body_joint_names) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: body_joint_positions
  {
    if (msg.body_joint_positions.size() == 0) {
      out << "body_joint_positions: []";
    } else {
      out << "body_joint_positions: [";
      size_t pending_items = msg.body_joint_positions.size();
      for (auto item : msg.body_joint_positions) {
        rosidl_generator_traits::value_to_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: model_output_type
  {
    out << "model_output_type: ";
    rosidl_generator_traits::value_to_yaml(msg.model_output_type, out);
    out << ", ";
  }

  // member: target_poses
  {
    if (msg.target_poses.size() == 0) {
      out << "target_poses: []";
    } else {
      out << "target_poses: [";
      size_t pending_items = msg.target_poses.size();
      for (auto item : msg.target_poses) {
        to_flow_style_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: target_joint_states
  {
    if (msg.target_joint_states.size() == 0) {
      out << "target_joint_states: []";
    } else {
      out << "target_joint_states: [";
      size_t pending_items = msg.target_joint_states.size();
      for (auto item : msg.target_joint_states) {
        to_flow_style_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: model_sleep_time
  {
    out << "model_sleep_time: ";
    rosidl_generator_traits::value_to_yaml(msg.model_sleep_time, out);
    out << ", ";
  }

  // member: trajectory_reference_time
  {
    out << "trajectory_reference_time: ";
    rosidl_generator_traits::value_to_yaml(msg.trajectory_reference_time, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const ModelPredict & msg,
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

  // member: body_joint_names
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.body_joint_names.size() == 0) {
      out << "body_joint_names: []\n";
    } else {
      out << "body_joint_names:\n";
      for (auto item : msg.body_joint_names) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }

  // member: body_joint_positions
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.body_joint_positions.size() == 0) {
      out << "body_joint_positions: []\n";
    } else {
      out << "body_joint_positions:\n";
      for (auto item : msg.body_joint_positions) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "- ";
        rosidl_generator_traits::value_to_yaml(item, out);
        out << "\n";
      }
    }
  }

  // member: model_output_type
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "model_output_type: ";
    rosidl_generator_traits::value_to_yaml(msg.model_output_type, out);
    out << "\n";
  }

  // member: target_poses
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.target_poses.size() == 0) {
      out << "target_poses: []\n";
    } else {
      out << "target_poses:\n";
      for (auto item : msg.target_poses) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "-\n";
        to_block_style_yaml(item, out, indentation + 2);
      }
    }
  }

  // member: target_joint_states
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.target_joint_states.size() == 0) {
      out << "target_joint_states: []\n";
    } else {
      out << "target_joint_states:\n";
      for (auto item : msg.target_joint_states) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "-\n";
        to_block_style_yaml(item, out, indentation + 2);
      }
    }
  }

  // member: model_sleep_time
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "model_sleep_time: ";
    rosidl_generator_traits::value_to_yaml(msg.model_sleep_time, out);
    out << "\n";
  }

  // member: trajectory_reference_time
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "trajectory_reference_time: ";
    rosidl_generator_traits::value_to_yaml(msg.trajectory_reference_time, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const ModelPredict & msg, bool use_flow_style = false)
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
  const genie_msgs::msg::ModelPredict & msg,
  std::ostream & out, size_t indentation = 0)
{
  genie_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use genie_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const genie_msgs::msg::ModelPredict & msg)
{
  return genie_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<genie_msgs::msg::ModelPredict>()
{
  return "genie_msgs::msg::ModelPredict";
}

template<>
inline const char * name<genie_msgs::msg::ModelPredict>()
{
  return "genie_msgs/msg/ModelPredict";
}

template<>
struct has_fixed_size<genie_msgs::msg::ModelPredict>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<genie_msgs::msg::ModelPredict>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<genie_msgs::msg::ModelPredict>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // GENIE_MSGS__MSG__DETAIL__MODEL_PREDICT__TRAITS_HPP_
