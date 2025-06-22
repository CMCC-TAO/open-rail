// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/Position.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__POSITION__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__POSITION__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/position__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_Position_agv_task_state
{
public:
  explicit Init_Position_agv_task_state(::genie_msgs::msg::Position & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::Position agv_task_state(::genie_msgs::msg::Position::_agv_task_state_type arg)
  {
    msg_.agv_task_state = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::Position msg_;
};

class Init_Position_motor_states
{
public:
  explicit Init_Position_motor_states(::genie_msgs::msg::Position & msg)
  : msg_(msg)
  {}
  Init_Position_agv_task_state motor_states(::genie_msgs::msg::Position::_motor_states_type arg)
  {
    msg_.motor_states = std::move(arg);
    return Init_Position_agv_task_state(msg_);
  }

private:
  ::genie_msgs::msg::Position msg_;
};

class Init_Position_yaw
{
public:
  explicit Init_Position_yaw(::genie_msgs::msg::Position & msg)
  : msg_(msg)
  {}
  Init_Position_motor_states yaw(::genie_msgs::msg::Position::_yaw_type arg)
  {
    msg_.yaw = std::move(arg);
    return Init_Position_motor_states(msg_);
  }

private:
  ::genie_msgs::msg::Position msg_;
};

class Init_Position_pitch
{
public:
  explicit Init_Position_pitch(::genie_msgs::msg::Position & msg)
  : msg_(msg)
  {}
  Init_Position_yaw pitch(::genie_msgs::msg::Position::_pitch_type arg)
  {
    msg_.pitch = std::move(arg);
    return Init_Position_yaw(msg_);
  }

private:
  ::genie_msgs::msg::Position msg_;
};

class Init_Position_roll
{
public:
  explicit Init_Position_roll(::genie_msgs::msg::Position & msg)
  : msg_(msg)
  {}
  Init_Position_pitch roll(::genie_msgs::msg::Position::_roll_type arg)
  {
    msg_.roll = std::move(arg);
    return Init_Position_pitch(msg_);
  }

private:
  ::genie_msgs::msg::Position msg_;
};

class Init_Position_gyro_z
{
public:
  explicit Init_Position_gyro_z(::genie_msgs::msg::Position & msg)
  : msg_(msg)
  {}
  Init_Position_roll gyro_z(::genie_msgs::msg::Position::_gyro_z_type arg)
  {
    msg_.gyro_z = std::move(arg);
    return Init_Position_roll(msg_);
  }

private:
  ::genie_msgs::msg::Position msg_;
};

class Init_Position_gyro_y
{
public:
  explicit Init_Position_gyro_y(::genie_msgs::msg::Position & msg)
  : msg_(msg)
  {}
  Init_Position_gyro_z gyro_y(::genie_msgs::msg::Position::_gyro_y_type arg)
  {
    msg_.gyro_y = std::move(arg);
    return Init_Position_gyro_z(msg_);
  }

private:
  ::genie_msgs::msg::Position msg_;
};

class Init_Position_gyro_x
{
public:
  explicit Init_Position_gyro_x(::genie_msgs::msg::Position & msg)
  : msg_(msg)
  {}
  Init_Position_gyro_y gyro_x(::genie_msgs::msg::Position::_gyro_x_type arg)
  {
    msg_.gyro_x = std::move(arg);
    return Init_Position_gyro_y(msg_);
  }

private:
  ::genie_msgs::msg::Position msg_;
};

class Init_Position_acc_z
{
public:
  explicit Init_Position_acc_z(::genie_msgs::msg::Position & msg)
  : msg_(msg)
  {}
  Init_Position_gyro_x acc_z(::genie_msgs::msg::Position::_acc_z_type arg)
  {
    msg_.acc_z = std::move(arg);
    return Init_Position_gyro_x(msg_);
  }

private:
  ::genie_msgs::msg::Position msg_;
};

class Init_Position_acc_y
{
public:
  explicit Init_Position_acc_y(::genie_msgs::msg::Position & msg)
  : msg_(msg)
  {}
  Init_Position_acc_z acc_y(::genie_msgs::msg::Position::_acc_y_type arg)
  {
    msg_.acc_y = std::move(arg);
    return Init_Position_acc_z(msg_);
  }

private:
  ::genie_msgs::msg::Position msg_;
};

class Init_Position_acc_x
{
public:
  explicit Init_Position_acc_x(::genie_msgs::msg::Position & msg)
  : msg_(msg)
  {}
  Init_Position_acc_y acc_x(::genie_msgs::msg::Position::_acc_x_type arg)
  {
    msg_.acc_x = std::move(arg);
    return Init_Position_acc_y(msg_);
  }

private:
  ::genie_msgs::msg::Position msg_;
};

class Init_Position_angular_speed
{
public:
  explicit Init_Position_angular_speed(::genie_msgs::msg::Position & msg)
  : msg_(msg)
  {}
  Init_Position_acc_x angular_speed(::genie_msgs::msg::Position::_angular_speed_type arg)
  {
    msg_.angular_speed = std::move(arg);
    return Init_Position_acc_x(msg_);
  }

private:
  ::genie_msgs::msg::Position msg_;
};

class Init_Position_linear_speed
{
public:
  explicit Init_Position_linear_speed(::genie_msgs::msg::Position & msg)
  : msg_(msg)
  {}
  Init_Position_angular_speed linear_speed(::genie_msgs::msg::Position::_linear_speed_type arg)
  {
    msg_.linear_speed = std::move(arg);
    return Init_Position_angular_speed(msg_);
  }

private:
  ::genie_msgs::msg::Position msg_;
};

class Init_Position_odom_angle
{
public:
  explicit Init_Position_odom_angle(::genie_msgs::msg::Position & msg)
  : msg_(msg)
  {}
  Init_Position_linear_speed odom_angle(::genie_msgs::msg::Position::_odom_angle_type arg)
  {
    msg_.odom_angle = std::move(arg);
    return Init_Position_linear_speed(msg_);
  }

private:
  ::genie_msgs::msg::Position msg_;
};

class Init_Position_odom_z
{
public:
  explicit Init_Position_odom_z(::genie_msgs::msg::Position & msg)
  : msg_(msg)
  {}
  Init_Position_odom_angle odom_z(::genie_msgs::msg::Position::_odom_z_type arg)
  {
    msg_.odom_z = std::move(arg);
    return Init_Position_odom_angle(msg_);
  }

private:
  ::genie_msgs::msg::Position msg_;
};

class Init_Position_odom_y
{
public:
  explicit Init_Position_odom_y(::genie_msgs::msg::Position & msg)
  : msg_(msg)
  {}
  Init_Position_odom_z odom_y(::genie_msgs::msg::Position::_odom_y_type arg)
  {
    msg_.odom_y = std::move(arg);
    return Init_Position_odom_z(msg_);
  }

private:
  ::genie_msgs::msg::Position msg_;
};

class Init_Position_odom_x
{
public:
  explicit Init_Position_odom_x(::genie_msgs::msg::Position & msg)
  : msg_(msg)
  {}
  Init_Position_odom_y odom_x(::genie_msgs::msg::Position::_odom_x_type arg)
  {
    msg_.odom_x = std::move(arg);
    return Init_Position_odom_y(msg_);
  }

private:
  ::genie_msgs::msg::Position msg_;
};

class Init_Position_agv_angle
{
public:
  explicit Init_Position_agv_angle(::genie_msgs::msg::Position & msg)
  : msg_(msg)
  {}
  Init_Position_odom_x agv_angle(::genie_msgs::msg::Position::_agv_angle_type arg)
  {
    msg_.agv_angle = std::move(arg);
    return Init_Position_odom_x(msg_);
  }

private:
  ::genie_msgs::msg::Position msg_;
};

class Init_Position_agv_pos_z
{
public:
  explicit Init_Position_agv_pos_z(::genie_msgs::msg::Position & msg)
  : msg_(msg)
  {}
  Init_Position_agv_angle agv_pos_z(::genie_msgs::msg::Position::_agv_pos_z_type arg)
  {
    msg_.agv_pos_z = std::move(arg);
    return Init_Position_agv_angle(msg_);
  }

private:
  ::genie_msgs::msg::Position msg_;
};

class Init_Position_agv_pos_y
{
public:
  explicit Init_Position_agv_pos_y(::genie_msgs::msg::Position & msg)
  : msg_(msg)
  {}
  Init_Position_agv_pos_z agv_pos_y(::genie_msgs::msg::Position::_agv_pos_y_type arg)
  {
    msg_.agv_pos_y = std::move(arg);
    return Init_Position_agv_pos_z(msg_);
  }

private:
  ::genie_msgs::msg::Position msg_;
};

class Init_Position_agv_pos_x
{
public:
  explicit Init_Position_agv_pos_x(::genie_msgs::msg::Position & msg)
  : msg_(msg)
  {}
  Init_Position_agv_pos_y agv_pos_x(::genie_msgs::msg::Position::_agv_pos_x_type arg)
  {
    msg_.agv_pos_x = std::move(arg);
    return Init_Position_agv_pos_y(msg_);
  }

private:
  ::genie_msgs::msg::Position msg_;
};

class Init_Position_position_conf
{
public:
  explicit Init_Position_position_conf(::genie_msgs::msg::Position & msg)
  : msg_(msg)
  {}
  Init_Position_agv_pos_x position_conf(::genie_msgs::msg::Position::_position_conf_type arg)
  {
    msg_.position_conf = std::move(arg);
    return Init_Position_agv_pos_x(msg_);
  }

private:
  ::genie_msgs::msg::Position msg_;
};

class Init_Position_agv_status
{
public:
  explicit Init_Position_agv_status(::genie_msgs::msg::Position & msg)
  : msg_(msg)
  {}
  Init_Position_position_conf agv_status(::genie_msgs::msg::Position::_agv_status_type arg)
  {
    msg_.agv_status = std::move(arg);
    return Init_Position_position_conf(msg_);
  }

private:
  ::genie_msgs::msg::Position msg_;
};

class Init_Position_header
{
public:
  Init_Position_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_Position_agv_status header(::genie_msgs::msg::Position::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_Position_agv_status(msg_);
  }

private:
  ::genie_msgs::msg::Position msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::Position>()
{
  return genie_msgs::msg::builder::Init_Position_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__POSITION__BUILDER_HPP_
