// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:srv/NoitomSetFreq.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__NOITOM_SET_FREQ__BUILDER_HPP_
#define GENIE_MSGS__SRV__DETAIL__NOITOM_SET_FREQ__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/srv/detail/noitom_set_freq__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_NoitomSetFreq_Request_frequency
{
public:
  Init_NoitomSetFreq_Request_frequency()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::genie_msgs::srv::NoitomSetFreq_Request frequency(::genie_msgs::srv::NoitomSetFreq_Request::_frequency_type arg)
  {
    msg_.frequency = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::NoitomSetFreq_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::NoitomSetFreq_Request>()
{
  return genie_msgs::srv::builder::Init_NoitomSetFreq_Request_frequency();
}

}  // namespace genie_msgs


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_NoitomSetFreq_Response_message
{
public:
  explicit Init_NoitomSetFreq_Response_message(::genie_msgs::srv::NoitomSetFreq_Response & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::NoitomSetFreq_Response message(::genie_msgs::srv::NoitomSetFreq_Response::_message_type arg)
  {
    msg_.message = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::NoitomSetFreq_Response msg_;
};

class Init_NoitomSetFreq_Response_current_frequency
{
public:
  explicit Init_NoitomSetFreq_Response_current_frequency(::genie_msgs::srv::NoitomSetFreq_Response & msg)
  : msg_(msg)
  {}
  Init_NoitomSetFreq_Response_message current_frequency(::genie_msgs::srv::NoitomSetFreq_Response::_current_frequency_type arg)
  {
    msg_.current_frequency = std::move(arg);
    return Init_NoitomSetFreq_Response_message(msg_);
  }

private:
  ::genie_msgs::srv::NoitomSetFreq_Response msg_;
};

class Init_NoitomSetFreq_Response_success
{
public:
  Init_NoitomSetFreq_Response_success()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_NoitomSetFreq_Response_current_frequency success(::genie_msgs::srv::NoitomSetFreq_Response::_success_type arg)
  {
    msg_.success = std::move(arg);
    return Init_NoitomSetFreq_Response_current_frequency(msg_);
  }

private:
  ::genie_msgs::srv::NoitomSetFreq_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::NoitomSetFreq_Response>()
{
  return genie_msgs::srv::builder::Init_NoitomSetFreq_Response_success();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__SRV__DETAIL__NOITOM_SET_FREQ__BUILDER_HPP_
