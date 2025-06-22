// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:srv/SetWifi.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__SET_WIFI__BUILDER_HPP_
#define GENIE_MSGS__SRV__DETAIL__SET_WIFI__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/srv/detail/set_wifi__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_SetWifi_Request_password
{
public:
  explicit Init_SetWifi_Request_password(::genie_msgs::srv::SetWifi_Request & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::SetWifi_Request password(::genie_msgs::srv::SetWifi_Request::_password_type arg)
  {
    msg_.password = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::SetWifi_Request msg_;
};

class Init_SetWifi_Request_ssid
{
public:
  Init_SetWifi_Request_ssid()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_SetWifi_Request_password ssid(::genie_msgs::srv::SetWifi_Request::_ssid_type arg)
  {
    msg_.ssid = std::move(arg);
    return Init_SetWifi_Request_password(msg_);
  }

private:
  ::genie_msgs::srv::SetWifi_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::SetWifi_Request>()
{
  return genie_msgs::srv::builder::Init_SetWifi_Request_ssid();
}

}  // namespace genie_msgs


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_SetWifi_Response_message
{
public:
  explicit Init_SetWifi_Response_message(::genie_msgs::srv::SetWifi_Response & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::SetWifi_Response message(::genie_msgs::srv::SetWifi_Response::_message_type arg)
  {
    msg_.message = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::SetWifi_Response msg_;
};

class Init_SetWifi_Response_success
{
public:
  Init_SetWifi_Response_success()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_SetWifi_Response_message success(::genie_msgs::srv::SetWifi_Response::_success_type arg)
  {
    msg_.success = std::move(arg);
    return Init_SetWifi_Response_message(msg_);
  }

private:
  ::genie_msgs::srv::SetWifi_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::SetWifi_Response>()
{
  return genie_msgs::srv::builder::Init_SetWifi_Response_success();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__SRV__DETAIL__SET_WIFI__BUILDER_HPP_
