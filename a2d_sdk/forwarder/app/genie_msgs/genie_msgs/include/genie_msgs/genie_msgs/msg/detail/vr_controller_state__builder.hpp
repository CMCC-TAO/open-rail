// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/VRControllerState.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__VR_CONTROLLER_STATE__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__VR_CONTROLLER_STATE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/vr_controller_state__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_VRControllerState_orientation
{
public:
  explicit Init_VRControllerState_orientation(::genie_msgs::msg::VRControllerState & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::VRControllerState orientation(::genie_msgs::msg::VRControllerState::_orientation_type arg)
  {
    msg_.orientation = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::VRControllerState msg_;
};

class Init_VRControllerState_position
{
public:
  explicit Init_VRControllerState_position(::genie_msgs::msg::VRControllerState & msg)
  : msg_(msg)
  {}
  Init_VRControllerState_orientation position(::genie_msgs::msg::VRControllerState::_position_type arg)
  {
    msg_.position = std::move(arg);
    return Init_VRControllerState_orientation(msg_);
  }

private:
  ::genie_msgs::msg::VRControllerState msg_;
};

class Init_VRControllerState_axis_click
{
public:
  explicit Init_VRControllerState_axis_click(::genie_msgs::msg::VRControllerState & msg)
  : msg_(msg)
  {}
  Init_VRControllerState_position axis_click(::genie_msgs::msg::VRControllerState::_axis_click_type arg)
  {
    msg_.axis_click = std::move(arg);
    return Init_VRControllerState_position(msg_);
  }

private:
  ::genie_msgs::msg::VRControllerState msg_;
};

class Init_VRControllerState_axis_y
{
public:
  explicit Init_VRControllerState_axis_y(::genie_msgs::msg::VRControllerState & msg)
  : msg_(msg)
  {}
  Init_VRControllerState_axis_click axis_y(::genie_msgs::msg::VRControllerState::_axis_y_type arg)
  {
    msg_.axis_y = std::move(arg);
    return Init_VRControllerState_axis_click(msg_);
  }

private:
  ::genie_msgs::msg::VRControllerState msg_;
};

class Init_VRControllerState_axis_x
{
public:
  explicit Init_VRControllerState_axis_x(::genie_msgs::msg::VRControllerState & msg)
  : msg_(msg)
  {}
  Init_VRControllerState_axis_y axis_x(::genie_msgs::msg::VRControllerState::_axis_x_type arg)
  {
    msg_.axis_x = std::move(arg);
    return Init_VRControllerState_axis_y(msg_);
  }

private:
  ::genie_msgs::msg::VRControllerState msg_;
};

class Init_VRControllerState_index_trig
{
public:
  explicit Init_VRControllerState_index_trig(::genie_msgs::msg::VRControllerState & msg)
  : msg_(msg)
  {}
  Init_VRControllerState_axis_x index_trig(::genie_msgs::msg::VRControllerState::_index_trig_type arg)
  {
    msg_.index_trig = std::move(arg);
    return Init_VRControllerState_axis_x(msg_);
  }

private:
  ::genie_msgs::msg::VRControllerState msg_;
};

class Init_VRControllerState_hand_trig
{
public:
  explicit Init_VRControllerState_hand_trig(::genie_msgs::msg::VRControllerState & msg)
  : msg_(msg)
  {}
  Init_VRControllerState_index_trig hand_trig(::genie_msgs::msg::VRControllerState::_hand_trig_type arg)
  {
    msg_.hand_trig = std::move(arg);
    return Init_VRControllerState_index_trig(msg_);
  }

private:
  ::genie_msgs::msg::VRControllerState msg_;
};

class Init_VRControllerState_key_two
{
public:
  explicit Init_VRControllerState_key_two(::genie_msgs::msg::VRControllerState & msg)
  : msg_(msg)
  {}
  Init_VRControllerState_hand_trig key_two(::genie_msgs::msg::VRControllerState::_key_two_type arg)
  {
    msg_.key_two = std::move(arg);
    return Init_VRControllerState_hand_trig(msg_);
  }

private:
  ::genie_msgs::msg::VRControllerState msg_;
};

class Init_VRControllerState_key_one
{
public:
  explicit Init_VRControllerState_key_one(::genie_msgs::msg::VRControllerState & msg)
  : msg_(msg)
  {}
  Init_VRControllerState_key_two key_one(::genie_msgs::msg::VRControllerState::_key_one_type arg)
  {
    msg_.key_one = std::move(arg);
    return Init_VRControllerState_key_two(msg_);
  }

private:
  ::genie_msgs::msg::VRControllerState msg_;
};

class Init_VRControllerState_id
{
public:
  explicit Init_VRControllerState_id(::genie_msgs::msg::VRControllerState & msg)
  : msg_(msg)
  {}
  Init_VRControllerState_key_one id(::genie_msgs::msg::VRControllerState::_id_type arg)
  {
    msg_.id = std::move(arg);
    return Init_VRControllerState_key_one(msg_);
  }

private:
  ::genie_msgs::msg::VRControllerState msg_;
};

class Init_VRControllerState_name
{
public:
  Init_VRControllerState_name()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_VRControllerState_id name(::genie_msgs::msg::VRControllerState::_name_type arg)
  {
    msg_.name = std::move(arg);
    return Init_VRControllerState_id(msg_);
  }

private:
  ::genie_msgs::msg::VRControllerState msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::VRControllerState>()
{
  return genie_msgs::msg::builder::Init_VRControllerState_name();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__VR_CONTROLLER_STATE__BUILDER_HPP_
