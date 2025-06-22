// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:srv/ForceCal.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__FORCE_CAL__BUILDER_HPP_
#define GENIE_MSGS__SRV__DETAIL__FORCE_CAL__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/srv/detail/force_cal__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_ForceCal_Request_block
{
public:
  explicit Init_ForceCal_Request_block(::genie_msgs::srv::ForceCal_Request & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::ForceCal_Request block(::genie_msgs::srv::ForceCal_Request::_block_type arg)
  {
    msg_.block = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::ForceCal_Request msg_;
};

class Init_ForceCal_Request_joint
{
public:
  explicit Init_ForceCal_Request_joint(::genie_msgs::srv::ForceCal_Request & msg)
  : msg_(msg)
  {}
  Init_ForceCal_Request_block joint(::genie_msgs::srv::ForceCal_Request::_joint_type arg)
  {
    msg_.joint = std::move(arg);
    return Init_ForceCal_Request_block(msg_);
  }

private:
  ::genie_msgs::srv::ForceCal_Request msg_;
};

class Init_ForceCal_Request_count
{
public:
  explicit Init_ForceCal_Request_count(::genie_msgs::srv::ForceCal_Request & msg)
  : msg_(msg)
  {}
  Init_ForceCal_Request_joint count(::genie_msgs::srv::ForceCal_Request::_count_type arg)
  {
    msg_.count = std::move(arg);
    return Init_ForceCal_Request_joint(msg_);
  }

private:
  ::genie_msgs::srv::ForceCal_Request msg_;
};

class Init_ForceCal_Request_force_id
{
public:
  explicit Init_ForceCal_Request_force_id(::genie_msgs::srv::ForceCal_Request & msg)
  : msg_(msg)
  {}
  Init_ForceCal_Request_count force_id(::genie_msgs::srv::ForceCal_Request::_force_id_type arg)
  {
    msg_.force_id = std::move(arg);
    return Init_ForceCal_Request_count(msg_);
  }

private:
  ::genie_msgs::srv::ForceCal_Request msg_;
};

class Init_ForceCal_Request_cal_cmd
{
public:
  explicit Init_ForceCal_Request_cal_cmd(::genie_msgs::srv::ForceCal_Request & msg)
  : msg_(msg)
  {}
  Init_ForceCal_Request_force_id cal_cmd(::genie_msgs::srv::ForceCal_Request::_cal_cmd_type arg)
  {
    msg_.cal_cmd = std::move(arg);
    return Init_ForceCal_Request_force_id(msg_);
  }

private:
  ::genie_msgs::srv::ForceCal_Request msg_;
};

class Init_ForceCal_Request_header
{
public:
  Init_ForceCal_Request_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ForceCal_Request_cal_cmd header(::genie_msgs::srv::ForceCal_Request::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_ForceCal_Request_cal_cmd(msg_);
  }

private:
  ::genie_msgs::srv::ForceCal_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::ForceCal_Request>()
{
  return genie_msgs::srv::builder::Init_ForceCal_Request_header();
}

}  // namespace genie_msgs


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_ForceCal_Response_exec_result
{
public:
  explicit Init_ForceCal_Response_exec_result(::genie_msgs::srv::ForceCal_Response & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::ForceCal_Response exec_result(::genie_msgs::srv::ForceCal_Response::_exec_result_type arg)
  {
    msg_.exec_result = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::ForceCal_Response msg_;
};

class Init_ForceCal_Response_res_header
{
public:
  Init_ForceCal_Response_res_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ForceCal_Response_exec_result res_header(::genie_msgs::srv::ForceCal_Response::_res_header_type arg)
  {
    msg_.res_header = std::move(arg);
    return Init_ForceCal_Response_exec_result(msg_);
  }

private:
  ::genie_msgs::srv::ForceCal_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::ForceCal_Response>()
{
  return genie_msgs::srv::builder::Init_ForceCal_Response_res_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__SRV__DETAIL__FORCE_CAL__BUILDER_HPP_
