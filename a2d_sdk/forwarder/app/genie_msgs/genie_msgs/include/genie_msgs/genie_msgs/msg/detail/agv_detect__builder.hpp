// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:msg/AGVDetect.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__AGV_DETECT__BUILDER_HPP_
#define GENIE_MSGS__MSG__DETAIL__AGV_DETECT__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/msg/detail/agv_detect__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace msg
{

namespace builder
{

class Init_AGVDetect_obs_conf
{
public:
  explicit Init_AGVDetect_obs_conf(::genie_msgs::msg::AGVDetect & msg)
  : msg_(msg)
  {}
  ::genie_msgs::msg::AGVDetect obs_conf(::genie_msgs::msg::AGVDetect::_obs_conf_type arg)
  {
    msg_.obs_conf = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::msg::AGVDetect msg_;
};

class Init_AGVDetect_obs_valid
{
public:
  explicit Init_AGVDetect_obs_valid(::genie_msgs::msg::AGVDetect & msg)
  : msg_(msg)
  {}
  Init_AGVDetect_obs_conf obs_valid(::genie_msgs::msg::AGVDetect::_obs_valid_type arg)
  {
    msg_.obs_valid = std::move(arg);
    return Init_AGVDetect_obs_conf(msg_);
  }

private:
  ::genie_msgs::msg::AGVDetect msg_;
};

class Init_AGVDetect_err_code
{
public:
  explicit Init_AGVDetect_err_code(::genie_msgs::msg::AGVDetect & msg)
  : msg_(msg)
  {}
  Init_AGVDetect_obs_valid err_code(::genie_msgs::msg::AGVDetect::_err_code_type arg)
  {
    msg_.err_code = std::move(arg);
    return Init_AGVDetect_obs_valid(msg_);
  }

private:
  ::genie_msgs::msg::AGVDetect msg_;
};

class Init_AGVDetect_status
{
public:
  explicit Init_AGVDetect_status(::genie_msgs::msg::AGVDetect & msg)
  : msg_(msg)
  {}
  Init_AGVDetect_err_code status(::genie_msgs::msg::AGVDetect::_status_type arg)
  {
    msg_.status = std::move(arg);
    return Init_AGVDetect_err_code(msg_);
  }

private:
  ::genie_msgs::msg::AGVDetect msg_;
};

class Init_AGVDetect_header
{
public:
  Init_AGVDetect_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_AGVDetect_status header(::genie_msgs::msg::AGVDetect::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_AGVDetect_status(msg_);
  }

private:
  ::genie_msgs::msg::AGVDetect msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::msg::AGVDetect>()
{
  return genie_msgs::msg::builder::Init_AGVDetect_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__AGV_DETECT__BUILDER_HPP_
