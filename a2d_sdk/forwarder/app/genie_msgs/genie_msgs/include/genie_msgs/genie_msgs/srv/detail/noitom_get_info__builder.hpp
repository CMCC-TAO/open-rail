// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:srv/NoitomGetInfo.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__NOITOM_GET_INFO__BUILDER_HPP_
#define GENIE_MSGS__SRV__DETAIL__NOITOM_GET_INFO__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/srv/detail/noitom_get_info__struct.hpp"
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
auto build<::genie_msgs::srv::NoitomGetInfo_Request>()
{
  return ::genie_msgs::srv::NoitomGetInfo_Request(rosidl_runtime_cpp::MessageInitialization::ZERO);
}

}  // namespace genie_msgs


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_NoitomGetInfo_Response_default_port
{
public:
  explicit Init_NoitomGetInfo_Response_default_port(::genie_msgs::srv::NoitomGetInfo_Response & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::NoitomGetInfo_Response default_port(::genie_msgs::srv::NoitomGetInfo_Response::_default_port_type arg)
  {
    msg_.default_port = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::NoitomGetInfo_Response msg_;
};

class Init_NoitomGetInfo_Response_default_ip
{
public:
  explicit Init_NoitomGetInfo_Response_default_ip(::genie_msgs::srv::NoitomGetInfo_Response & msg)
  : msg_(msg)
  {}
  Init_NoitomGetInfo_Response_default_port default_ip(::genie_msgs::srv::NoitomGetInfo_Response::_default_ip_type arg)
  {
    msg_.default_ip = std::move(arg);
    return Init_NoitomGetInfo_Response_default_port(msg_);
  }

private:
  ::genie_msgs::srv::NoitomGetInfo_Response msg_;
};

class Init_NoitomGetInfo_Response_hardware_date
{
public:
  explicit Init_NoitomGetInfo_Response_hardware_date(::genie_msgs::srv::NoitomGetInfo_Response & msg)
  : msg_(msg)
  {}
  Init_NoitomGetInfo_Response_default_ip hardware_date(::genie_msgs::srv::NoitomGetInfo_Response::_hardware_date_type arg)
  {
    msg_.hardware_date = std::move(arg);
    return Init_NoitomGetInfo_Response_default_ip(msg_);
  }

private:
  ::genie_msgs::srv::NoitomGetInfo_Response msg_;
};

class Init_NoitomGetInfo_Response_software_version
{
public:
  explicit Init_NoitomGetInfo_Response_software_version(::genie_msgs::srv::NoitomGetInfo_Response & msg)
  : msg_(msg)
  {}
  Init_NoitomGetInfo_Response_hardware_date software_version(::genie_msgs::srv::NoitomGetInfo_Response::_software_version_type arg)
  {
    msg_.software_version = std::move(arg);
    return Init_NoitomGetInfo_Response_hardware_date(msg_);
  }

private:
  ::genie_msgs::srv::NoitomGetInfo_Response msg_;
};

class Init_NoitomGetInfo_Response_device_sn
{
public:
  Init_NoitomGetInfo_Response_device_sn()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_NoitomGetInfo_Response_software_version device_sn(::genie_msgs::srv::NoitomGetInfo_Response::_device_sn_type arg)
  {
    msg_.device_sn = std::move(arg);
    return Init_NoitomGetInfo_Response_software_version(msg_);
  }

private:
  ::genie_msgs::srv::NoitomGetInfo_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::NoitomGetInfo_Response>()
{
  return genie_msgs::srv::builder::Init_NoitomGetInfo_Response_device_sn();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__SRV__DETAIL__NOITOM_GET_INFO__BUILDER_HPP_
