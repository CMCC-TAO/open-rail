// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/VRNetwork.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__VR_NETWORK__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__VR_NETWORK__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/vr_network__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_VRNetwork_remote_ip_address
{
public:
  explicit Init_VRNetwork_remote_ip_address(::genie_msgs::msg::VRNetwork & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::VRNetwork remote_ip_address(::genie_msgs::msg::VRNetwork::_remote_ip_address_type arg)
  {
    msg_.remote_ip_address = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::VRNetwork msg_;
};

class Init_VRNetwork_ip_address
{
public:
  explicit Init_VRNetwork_ip_address(::genie_msgs::msg::VRNetwork & msg)
  : msg_(msg)
  {}
  Init_VRNetwork_remote_ip_address ip_address(::genie_msgs::msg::VRNetwork::_ip_address_type arg)
  {
    msg_.ip_address = std::move(arg);
    return Init_VRNetwork_remote_ip_address(msg_);
  }

private:
  ::genie_msgs::msg::VRNetwork msg_;
};

class Init_VRNetwork_frequency
{
public:
  explicit Init_VRNetwork_frequency(::genie_msgs::msg::VRNetwork & msg)
  : msg_(msg)
  {}
  Init_VRNetwork_ip_address frequency(::genie_msgs::msg::VRNetwork::_frequency_type arg)
  {
    msg_.frequency = std::move(arg);
    return Init_VRNetwork_ip_address(msg_);
  }

private:
  ::genie_msgs::msg::VRNetwork msg_;
};

class Init_VRNetwork_latency
{
public:
  explicit Init_VRNetwork_latency(::genie_msgs::msg::VRNetwork & msg)
  : msg_(msg)
  {}
  Init_VRNetwork_frequency latency(::genie_msgs::msg::VRNetwork::_latency_type arg)
  {
    msg_.latency = std::move(arg);
    return Init_VRNetwork_frequency(msg_);
  }

private:
  ::genie_msgs::msg::VRNetwork msg_;
};

class Init_VRNetwork_packet_loss_rate
{
public:
  explicit Init_VRNetwork_packet_loss_rate(::genie_msgs::msg::VRNetwork & msg)
  : msg_(msg)
  {}
  Init_VRNetwork_latency packet_loss_rate(::genie_msgs::msg::VRNetwork::_packet_loss_rate_type arg)
  {
    msg_.packet_loss_rate = std::move(arg);
    return Init_VRNetwork_latency(msg_);
  }

private:
  ::genie_msgs::msg::VRNetwork msg_;
};

class Init_VRNetwork_is_connected
{
public:
  explicit Init_VRNetwork_is_connected(::genie_msgs::msg::VRNetwork & msg)
  : msg_(msg)
  {}
  Init_VRNetwork_packet_loss_rate is_connected(::genie_msgs::msg::VRNetwork::_is_connected_type arg)
  {
    msg_.is_connected = std::move(arg);
    return Init_VRNetwork_packet_loss_rate(msg_);
  }

private:
  ::genie_msgs::msg::VRNetwork msg_;
};

class Init_VRNetwork_device_name
{
public:
  explicit Init_VRNetwork_device_name(::genie_msgs::msg::VRNetwork & msg)
  : msg_(msg)
  {}
  Init_VRNetwork_is_connected device_name(::genie_msgs::msg::VRNetwork::_device_name_type arg)
  {
    msg_.device_name = std::move(arg);
    return Init_VRNetwork_is_connected(msg_);
  }

private:
  ::genie_msgs::msg::VRNetwork msg_;
};

class Init_VRNetwork_header
{
public:
  Init_VRNetwork_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_VRNetwork_device_name header(::genie_msgs::msg::VRNetwork::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_VRNetwork_device_name(msg_);
  }

private:
  ::genie_msgs::msg::VRNetwork msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::VRNetwork>()
{
  return genie_msgs::msg::builder::Init_VRNetwork_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__VR_NETWORK__BUILDER_HPP_
