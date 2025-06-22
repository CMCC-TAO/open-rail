// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/AGVTaskState.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__AGV_TASK_STATE__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__AGV_TASK_STATE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/agv_task_state__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_AGVTaskState_finish_state
{
public:
  explicit Init_AGVTaskState_finish_state(::genie_msgs::msg::AGVTaskState & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::AGVTaskState finish_state(::genie_msgs::msg::AGVTaskState::_finish_state_type arg)
  {
    msg_.finish_state = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::AGVTaskState msg_;
};

class Init_AGVTaskState_curr_station_idx
{
public:
  explicit Init_AGVTaskState_curr_station_idx(::genie_msgs::msg::AGVTaskState & msg)
  : msg_(msg)
  {}
  Init_AGVTaskState_finish_state curr_station_idx(::genie_msgs::msg::AGVTaskState::_curr_station_idx_type arg)
  {
    msg_.curr_station_idx = std::move(arg);
    return Init_AGVTaskState_finish_state(msg_);
  }

private:
  ::genie_msgs::msg::AGVTaskState msg_;
};

class Init_AGVTaskState_task_reqid
{
public:
  explicit Init_AGVTaskState_task_reqid(::genie_msgs::msg::AGVTaskState & msg)
  : msg_(msg)
  {}
  Init_AGVTaskState_curr_station_idx task_reqid(::genie_msgs::msg::AGVTaskState::_task_reqid_type arg)
  {
    msg_.task_reqid = std::move(arg);
    return Init_AGVTaskState_curr_station_idx(msg_);
  }

private:
  ::genie_msgs::msg::AGVTaskState msg_;
};

class Init_AGVTaskState_task_uuid
{
public:
  explicit Init_AGVTaskState_task_uuid(::genie_msgs::msg::AGVTaskState & msg)
  : msg_(msg)
  {}
  Init_AGVTaskState_task_reqid task_uuid(::genie_msgs::msg::AGVTaskState::_task_uuid_type arg)
  {
    msg_.task_uuid = std::move(arg);
    return Init_AGVTaskState_task_reqid(msg_);
  }

private:
  ::genie_msgs::msg::AGVTaskState msg_;
};

class Init_AGVTaskState_header
{
public:
  Init_AGVTaskState_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_AGVTaskState_task_uuid header(::genie_msgs::msg::AGVTaskState::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_AGVTaskState_task_uuid(msg_);
  }

private:
  ::genie_msgs::msg::AGVTaskState msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::AGVTaskState>()
{
  return genie_msgs::msg::builder::Init_AGVTaskState_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__AGV_TASK_STATE__BUILDER_HPP_
