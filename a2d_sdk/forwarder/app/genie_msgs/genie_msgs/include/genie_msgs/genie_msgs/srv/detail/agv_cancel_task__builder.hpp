// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:srv/AGVCancelTask.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__AGV_CANCEL_TASK__BUILDER_HPP_
#define GENIE_MSGS__SRV__DETAIL__AGV_CANCEL_TASK__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/srv/detail/agv_cancel_task__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_AGVCancelTask_Request_task_uuid
{
public:
  explicit Init_AGVCancelTask_Request_task_uuid(::genie_msgs::srv::AGVCancelTask_Request & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::AGVCancelTask_Request task_uuid(::genie_msgs::srv::AGVCancelTask_Request::_task_uuid_type arg)
  {
    msg_.task_uuid = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::AGVCancelTask_Request msg_;
};

class Init_AGVCancelTask_Request_header
{
public:
  Init_AGVCancelTask_Request_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_AGVCancelTask_Request_task_uuid header(::genie_msgs::srv::AGVCancelTask_Request::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_AGVCancelTask_Request_task_uuid(msg_);
  }

private:
  ::genie_msgs::srv::AGVCancelTask_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::AGVCancelTask_Request>()
{
  return genie_msgs::srv::builder::Init_AGVCancelTask_Request_header();
}

}  // namespace genie_msgs


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_AGVCancelTask_Response_task_uuid
{
public:
  explicit Init_AGVCancelTask_Response_task_uuid(::genie_msgs::srv::AGVCancelTask_Response & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::AGVCancelTask_Response task_uuid(::genie_msgs::srv::AGVCancelTask_Response::_task_uuid_type arg)
  {
    msg_.task_uuid = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::AGVCancelTask_Response msg_;
};

class Init_AGVCancelTask_Response_ret_code
{
public:
  explicit Init_AGVCancelTask_Response_ret_code(::genie_msgs::srv::AGVCancelTask_Response & msg)
  : msg_(msg)
  {}
  Init_AGVCancelTask_Response_task_uuid ret_code(::genie_msgs::srv::AGVCancelTask_Response::_ret_code_type arg)
  {
    msg_.ret_code = std::move(arg);
    return Init_AGVCancelTask_Response_task_uuid(msg_);
  }

private:
  ::genie_msgs::srv::AGVCancelTask_Response msg_;
};

class Init_AGVCancelTask_Response_req_result
{
public:
  explicit Init_AGVCancelTask_Response_req_result(::genie_msgs::srv::AGVCancelTask_Response & msg)
  : msg_(msg)
  {}
  Init_AGVCancelTask_Response_ret_code req_result(::genie_msgs::srv::AGVCancelTask_Response::_req_result_type arg)
  {
    msg_.req_result = std::move(arg);
    return Init_AGVCancelTask_Response_ret_code(msg_);
  }

private:
  ::genie_msgs::srv::AGVCancelTask_Response msg_;
};

class Init_AGVCancelTask_Response_res_header
{
public:
  Init_AGVCancelTask_Response_res_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_AGVCancelTask_Response_req_result res_header(::genie_msgs::srv::AGVCancelTask_Response::_res_header_type arg)
  {
    msg_.res_header = std::move(arg);
    return Init_AGVCancelTask_Response_req_result(msg_);
  }

private:
  ::genie_msgs::srv::AGVCancelTask_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::AGVCancelTask_Response>()
{
  return genie_msgs::srv::builder::Init_AGVCancelTask_Response_res_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__SRV__DETAIL__AGV_CANCEL_TASK__BUILDER_HPP_
