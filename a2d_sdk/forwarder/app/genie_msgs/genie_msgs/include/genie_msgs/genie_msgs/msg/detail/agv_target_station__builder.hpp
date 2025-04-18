// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/AGVTargetStation.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__AGV_TARGET_STATION__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__AGV_TARGET_STATION__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/agv_target_station__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_AGVTargetStation_station_action
{
public:
  explicit Init_AGVTargetStation_station_action(::genie_msgs::msg::AGVTargetStation & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::AGVTargetStation station_action(::genie_msgs::msg::AGVTargetStation::_station_action_type arg)
  {
    msg_.station_action = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::AGVTargetStation msg_;
};

class Init_AGVTargetStation_station_name
{
public:
  explicit Init_AGVTargetStation_station_name(::genie_msgs::msg::AGVTargetStation & msg)
  : msg_(msg)
  {}
  Init_AGVTargetStation_station_action station_name(::genie_msgs::msg::AGVTargetStation::_station_name_type arg)
  {
    msg_.station_name = std::move(arg);
    return Init_AGVTargetStation_station_action(msg_);
  }

private:
  ::genie_msgs::msg::AGVTargetStation msg_;
};

class Init_AGVTargetStation_station_id
{
public:
  explicit Init_AGVTargetStation_station_id(::genie_msgs::msg::AGVTargetStation & msg)
  : msg_(msg)
  {}
  Init_AGVTargetStation_station_name station_id(::genie_msgs::msg::AGVTargetStation::_station_id_type arg)
  {
    msg_.station_id = std::move(arg);
    return Init_AGVTargetStation_station_name(msg_);
  }

private:
  ::genie_msgs::msg::AGVTargetStation msg_;
};

class Init_AGVTargetStation_header
{
public:
  Init_AGVTargetStation_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_AGVTargetStation_station_id header(::genie_msgs::msg::AGVTargetStation::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_AGVTargetStation_station_id(msg_);
  }

private:
  ::genie_msgs::msg::AGVTargetStation msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::AGVTargetStation>()
{
  return genie_msgs::msg::builder::Init_AGVTargetStation_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__AGV_TARGET_STATION__BUILDER_HPP_
