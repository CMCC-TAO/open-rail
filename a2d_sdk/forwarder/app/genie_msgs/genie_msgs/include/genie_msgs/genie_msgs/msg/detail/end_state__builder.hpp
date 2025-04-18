// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/EndState.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__END_STATE__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__END_STATE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/end_state__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_EndState_end_state
{
public:
  explicit Init_EndState_end_state(::genie_msgs::msg::EndState & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::EndState end_state(::genie_msgs::msg::EndState::_end_state_type arg)
  {
    msg_.end_state = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::EndState msg_;
};

class Init_EndState_controlled
{
public:
  explicit Init_EndState_controlled(::genie_msgs::msg::EndState & msg)
  : msg_(msg)
  {}
  Init_EndState_end_state controlled(::genie_msgs::msg::EndState::_controlled_type arg)
  {
    msg_.controlled = std::move(arg);
    return Init_EndState_end_state(msg_);
  }

private:
  ::genie_msgs::msg::EndState msg_;
};

class Init_EndState_header
{
public:
  Init_EndState_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_EndState_controlled header(::genie_msgs::msg::EndState::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_EndState_controlled(msg_);
  }

private:
  ::genie_msgs::msg::EndState msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::EndState>()
{
  return genie_msgs::msg::builder::Init_EndState_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__END_STATE__BUILDER_HPP_
