// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:srv/NoitomRestart.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__NOITOM_RESTART__BUILDER_HPP_
#define GENIE_MSGS__SRV__DETAIL__NOITOM_RESTART__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/srv/detail/noitom_restart__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace srv
{


}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::NoitomRestart_Request>()
{
  return ::genie_msgs::srv::NoitomRestart_Request(rosidl_runtime_cpp::MessageInitialization::ZERO);
}

}  // namespace genie_msgs


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_NoitomRestart_Response_message
{
public:
  explicit Init_NoitomRestart_Response_message(::genie_msgs::srv::NoitomRestart_Response & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::NoitomRestart_Response message(::genie_msgs::srv::NoitomRestart_Response::_message_type arg)
  {
    msg_.message = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::NoitomRestart_Response msg_;
};

class Init_NoitomRestart_Response_success
{
public:
  Init_NoitomRestart_Response_success()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_NoitomRestart_Response_message success(::genie_msgs::srv::NoitomRestart_Response::_success_type arg)
  {
    msg_.success = std::move(arg);
    return Init_NoitomRestart_Response_message(msg_);
  }

private:
  ::genie_msgs::srv::NoitomRestart_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::NoitomRestart_Response>()
{
  return genie_msgs::srv::builder::Init_NoitomRestart_Response_success();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__SRV__DETAIL__NOITOM_RESTART__BUILDER_HPP_
