// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:srv/AGVControl.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__AGV_CONTROL__BUILDER_HPP_
#define GENIE_MSGS__SRV__DETAIL__AGV_CONTROL__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/srv/detail/agv_control__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_AGVControl_Request_control
{
public:
  explicit Init_AGVControl_Request_control(::genie_msgs::srv::AGVControl_Request & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::AGVControl_Request control(::genie_msgs::srv::AGVControl_Request::_control_type arg)
  {
    msg_.control = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::AGVControl_Request msg_;
};

class Init_AGVControl_Request_req_header
{
public:
  Init_AGVControl_Request_req_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_AGVControl_Request_control req_header(::genie_msgs::srv::AGVControl_Request::_req_header_type arg)
  {
    msg_.req_header = std::move(arg);
    return Init_AGVControl_Request_control(msg_);
  }

private:
  ::genie_msgs::srv::AGVControl_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::AGVControl_Request>()
{
  return genie_msgs::srv::builder::Init_AGVControl_Request_req_header();
}

}  // namespace genie_msgs


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_AGVControl_Response_exec_result
{
public:
  explicit Init_AGVControl_Response_exec_result(::genie_msgs::srv::AGVControl_Response & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::AGVControl_Response exec_result(::genie_msgs::srv::AGVControl_Response::_exec_result_type arg)
  {
    msg_.exec_result = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::AGVControl_Response msg_;
};

class Init_AGVControl_Response_res_header
{
public:
  Init_AGVControl_Response_res_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_AGVControl_Response_exec_result res_header(::genie_msgs::srv::AGVControl_Response::_res_header_type arg)
  {
    msg_.res_header = std::move(arg);
    return Init_AGVControl_Response_exec_result(msg_);
  }

private:
  ::genie_msgs::srv::AGVControl_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::AGVControl_Response>()
{
  return genie_msgs::srv::builder::Init_AGVControl_Response_res_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__SRV__DETAIL__AGV_CONTROL__BUILDER_HPP_
