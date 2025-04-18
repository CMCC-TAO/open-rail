// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:srv/NoitomCalibrate.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__NOITOM_CALIBRATE__BUILDER_HPP_
#define GENIE_MSGS__SRV__DETAIL__NOITOM_CALIBRATE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/srv/detail/noitom_calibrate__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_NoitomCalibrate_Request_block
{
public:
  explicit Init_NoitomCalibrate_Request_block(::genie_msgs::srv::NoitomCalibrate_Request & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::NoitomCalibrate_Request block(::genie_msgs::srv::NoitomCalibrate_Request::_block_type arg)
  {
    msg_.block = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::NoitomCalibrate_Request msg_;
};

class Init_NoitomCalibrate_Request_cali_cmd
{
public:
  explicit Init_NoitomCalibrate_Request_cali_cmd(::genie_msgs::srv::NoitomCalibrate_Request & msg)
  : msg_(msg)
  {}
  Init_NoitomCalibrate_Request_block cali_cmd(::genie_msgs::srv::NoitomCalibrate_Request::_cali_cmd_type arg)
  {
    msg_.cali_cmd = std::move(arg);
    return Init_NoitomCalibrate_Request_block(msg_);
  }

private:
  ::genie_msgs::srv::NoitomCalibrate_Request msg_;
};

class Init_NoitomCalibrate_Request_header
{
public:
  Init_NoitomCalibrate_Request_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_NoitomCalibrate_Request_cali_cmd header(::genie_msgs::srv::NoitomCalibrate_Request::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_NoitomCalibrate_Request_cali_cmd(msg_);
  }

private:
  ::genie_msgs::srv::NoitomCalibrate_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::NoitomCalibrate_Request>()
{
  return genie_msgs::srv::builder::Init_NoitomCalibrate_Request_header();
}

}  // namespace genie_msgs


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_NoitomCalibrate_Response_exec_result
{
public:
  explicit Init_NoitomCalibrate_Response_exec_result(::genie_msgs::srv::NoitomCalibrate_Response & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::NoitomCalibrate_Response exec_result(::genie_msgs::srv::NoitomCalibrate_Response::_exec_result_type arg)
  {
    msg_.exec_result = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::NoitomCalibrate_Response msg_;
};

class Init_NoitomCalibrate_Response_res_header
{
public:
  Init_NoitomCalibrate_Response_res_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_NoitomCalibrate_Response_exec_result res_header(::genie_msgs::srv::NoitomCalibrate_Response::_res_header_type arg)
  {
    msg_.res_header = std::move(arg);
    return Init_NoitomCalibrate_Response_exec_result(msg_);
  }

private:
  ::genie_msgs::srv::NoitomCalibrate_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::NoitomCalibrate_Response>()
{
  return genie_msgs::srv::builder::Init_NoitomCalibrate_Response_res_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__SRV__DETAIL__NOITOM_CALIBRATE__BUILDER_HPP_
