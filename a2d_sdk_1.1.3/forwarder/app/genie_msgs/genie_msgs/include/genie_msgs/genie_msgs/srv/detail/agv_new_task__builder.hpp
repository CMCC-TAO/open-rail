// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:srv/AGVNewTask.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__AGV_NEW_TASK__BUILDER_HPP_
#define GENIE_MSGS__SRV__DETAIL__AGV_NEW_TASK__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/srv/detail/agv_new_task__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_AGVNewTask_Request_is_loop
{
public:
  explicit Init_AGVNewTask_Request_is_loop(::genie_msgs::srv::AGVNewTask_Request & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::AGVNewTask_Request is_loop(::genie_msgs::srv::AGVNewTask_Request::_is_loop_type arg)
  {
    msg_.is_loop = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::AGVNewTask_Request msg_;
};

class Init_AGVNewTask_Request_target_station_list
{
public:
  explicit Init_AGVNewTask_Request_target_station_list(::genie_msgs::srv::AGVNewTask_Request & msg)
  : msg_(msg)
  {}
  Init_AGVNewTask_Request_is_loop target_station_list(::genie_msgs::srv::AGVNewTask_Request::_target_station_list_type arg)
  {
    msg_.target_station_list = std::move(arg);
    return Init_AGVNewTask_Request_is_loop(msg_);
  }

private:
  ::genie_msgs::srv::AGVNewTask_Request msg_;
};

class Init_AGVNewTask_Request_map_id
{
public:
  explicit Init_AGVNewTask_Request_map_id(::genie_msgs::srv::AGVNewTask_Request & msg)
  : msg_(msg)
  {}
  Init_AGVNewTask_Request_target_station_list map_id(::genie_msgs::srv::AGVNewTask_Request::_map_id_type arg)
  {
    msg_.map_id = std::move(arg);
    return Init_AGVNewTask_Request_target_station_list(msg_);
  }

private:
  ::genie_msgs::srv::AGVNewTask_Request msg_;
};

class Init_AGVNewTask_Request_task_reqid
{
public:
  explicit Init_AGVNewTask_Request_task_reqid(::genie_msgs::srv::AGVNewTask_Request & msg)
  : msg_(msg)
  {}
  Init_AGVNewTask_Request_map_id task_reqid(::genie_msgs::srv::AGVNewTask_Request::_task_reqid_type arg)
  {
    msg_.task_reqid = std::move(arg);
    return Init_AGVNewTask_Request_map_id(msg_);
  }

private:
  ::genie_msgs::srv::AGVNewTask_Request msg_;
};

class Init_AGVNewTask_Request_header
{
public:
  Init_AGVNewTask_Request_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_AGVNewTask_Request_task_reqid header(::genie_msgs::srv::AGVNewTask_Request::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_AGVNewTask_Request_task_reqid(msg_);
  }

private:
  ::genie_msgs::srv::AGVNewTask_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::AGVNewTask_Request>()
{
  return genie_msgs::srv::builder::Init_AGVNewTask_Request_header();
}

}  // namespace genie_msgs


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_AGVNewTask_Response_task_reqid
{
public:
  explicit Init_AGVNewTask_Response_task_reqid(::genie_msgs::srv::AGVNewTask_Response & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::AGVNewTask_Response task_reqid(::genie_msgs::srv::AGVNewTask_Response::_task_reqid_type arg)
  {
    msg_.task_reqid = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::AGVNewTask_Response msg_;
};

class Init_AGVNewTask_Response_task_uuid
{
public:
  explicit Init_AGVNewTask_Response_task_uuid(::genie_msgs::srv::AGVNewTask_Response & msg)
  : msg_(msg)
  {}
  Init_AGVNewTask_Response_task_reqid task_uuid(::genie_msgs::srv::AGVNewTask_Response::_task_uuid_type arg)
  {
    msg_.task_uuid = std::move(arg);
    return Init_AGVNewTask_Response_task_reqid(msg_);
  }

private:
  ::genie_msgs::srv::AGVNewTask_Response msg_;
};

class Init_AGVNewTask_Response_ret_code
{
public:
  explicit Init_AGVNewTask_Response_ret_code(::genie_msgs::srv::AGVNewTask_Response & msg)
  : msg_(msg)
  {}
  Init_AGVNewTask_Response_task_uuid ret_code(::genie_msgs::srv::AGVNewTask_Response::_ret_code_type arg)
  {
    msg_.ret_code = std::move(arg);
    return Init_AGVNewTask_Response_task_uuid(msg_);
  }

private:
  ::genie_msgs::srv::AGVNewTask_Response msg_;
};

class Init_AGVNewTask_Response_req_result
{
public:
  explicit Init_AGVNewTask_Response_req_result(::genie_msgs::srv::AGVNewTask_Response & msg)
  : msg_(msg)
  {}
  Init_AGVNewTask_Response_ret_code req_result(::genie_msgs::srv::AGVNewTask_Response::_req_result_type arg)
  {
    msg_.req_result = std::move(arg);
    return Init_AGVNewTask_Response_ret_code(msg_);
  }

private:
  ::genie_msgs::srv::AGVNewTask_Response msg_;
};

class Init_AGVNewTask_Response_res_header
{
public:
  Init_AGVNewTask_Response_res_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_AGVNewTask_Response_req_result res_header(::genie_msgs::srv::AGVNewTask_Response::_res_header_type arg)
  {
    msg_.res_header = std::move(arg);
    return Init_AGVNewTask_Response_req_result(msg_);
  }

private:
  ::genie_msgs::srv::AGVNewTask_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::AGVNewTask_Response>()
{
  return genie_msgs::srv::builder::Init_AGVNewTask_Response_res_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__SRV__DETAIL__AGV_NEW_TASK__BUILDER_HPP_
