// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:srv/FeatSetWorkMode.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__FEAT_SET_WORK_MODE__BUILDER_HPP_
#define GENIE_MSGS__SRV__DETAIL__FEAT_SET_WORK_MODE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/srv/detail/feat_set_work_mode__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_FeatSetWorkMode_Request_work_mode
{
public:
  explicit Init_FeatSetWorkMode_Request_work_mode(::genie_msgs::srv::FeatSetWorkMode_Request & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::FeatSetWorkMode_Request work_mode(::genie_msgs::srv::FeatSetWorkMode_Request::_work_mode_type arg)
  {
    msg_.work_mode = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::FeatSetWorkMode_Request msg_;
};

class Init_FeatSetWorkMode_Request_header
{
public:
  Init_FeatSetWorkMode_Request_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_FeatSetWorkMode_Request_work_mode header(::genie_msgs::srv::FeatSetWorkMode_Request::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_FeatSetWorkMode_Request_work_mode(msg_);
  }

private:
  ::genie_msgs::srv::FeatSetWorkMode_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::FeatSetWorkMode_Request>()
{
  return genie_msgs::srv::builder::Init_FeatSetWorkMode_Request_header();
}

}  // namespace genie_msgs


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_FeatSetWorkMode_Response_exec_result
{
public:
  explicit Init_FeatSetWorkMode_Response_exec_result(::genie_msgs::srv::FeatSetWorkMode_Response & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::FeatSetWorkMode_Response exec_result(::genie_msgs::srv::FeatSetWorkMode_Response::_exec_result_type arg)
  {
    msg_.exec_result = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::FeatSetWorkMode_Response msg_;
};

class Init_FeatSetWorkMode_Response_res_header
{
public:
  Init_FeatSetWorkMode_Response_res_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_FeatSetWorkMode_Response_exec_result res_header(::genie_msgs::srv::FeatSetWorkMode_Response::_res_header_type arg)
  {
    msg_.res_header = std::move(arg);
    return Init_FeatSetWorkMode_Response_exec_result(msg_);
  }

private:
  ::genie_msgs::srv::FeatSetWorkMode_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::FeatSetWorkMode_Response>()
{
  return genie_msgs::srv::builder::Init_FeatSetWorkMode_Response_res_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__SRV__DETAIL__FEAT_SET_WORK_MODE__BUILDER_HPP_
