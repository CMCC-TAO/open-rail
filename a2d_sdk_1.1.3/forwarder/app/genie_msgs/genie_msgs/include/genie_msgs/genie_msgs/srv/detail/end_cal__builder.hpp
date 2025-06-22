// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from genie_msgs:srv/EndCal.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__END_CAL__BUILDER_HPP_
#define GENIE_MSGS__SRV__DETAIL__END_CAL__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "genie_msgs/srv/detail/end_cal__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_EndCal_Request_block
{
public:
  explicit Init_EndCal_Request_block(::genie_msgs::srv::EndCal_Request & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::EndCal_Request block(::genie_msgs::srv::EndCal_Request::_block_type arg)
  {
    msg_.block = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::EndCal_Request msg_;
};

class Init_EndCal_Request_end_sel
{
public:
  explicit Init_EndCal_Request_end_sel(::genie_msgs::srv::EndCal_Request & msg)
  : msg_(msg)
  {}
  Init_EndCal_Request_block end_sel(::genie_msgs::srv::EndCal_Request::_end_sel_type arg)
  {
    msg_.end_sel = std::move(arg);
    return Init_EndCal_Request_block(msg_);
  }

private:
  ::genie_msgs::srv::EndCal_Request msg_;
};

class Init_EndCal_Request_header
{
public:
  Init_EndCal_Request_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_EndCal_Request_end_sel header(::genie_msgs::srv::EndCal_Request::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_EndCal_Request_end_sel(msg_);
  }

private:
  ::genie_msgs::srv::EndCal_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::EndCal_Request>()
{
  return genie_msgs::srv::builder::Init_EndCal_Request_header();
}

}  // namespace genie_msgs


namespace genie_msgs
{

namespace srv
{

namespace builder
{

class Init_EndCal_Response_exec_result
{
public:
  explicit Init_EndCal_Response_exec_result(::genie_msgs::srv::EndCal_Response & msg)
  : msg_(msg)
  {}
  ::genie_msgs::srv::EndCal_Response exec_result(::genie_msgs::srv::EndCal_Response::_exec_result_type arg)
  {
    msg_.exec_result = std::move(arg);
    return std::move(msg_);
  }

private:
  ::genie_msgs::srv::EndCal_Response msg_;
};

class Init_EndCal_Response_res_header
{
public:
  Init_EndCal_Response_res_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_EndCal_Response_exec_result res_header(::genie_msgs::srv::EndCal_Response::_res_header_type arg)
  {
    msg_.res_header = std::move(arg);
    return Init_EndCal_Response_exec_result(msg_);
  }

private:
  ::genie_msgs::srv::EndCal_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::genie_msgs::srv::EndCal_Response>()
{
  return genie_msgs::srv::builder::Init_EndCal_Response_res_header();
}

}  // namespace genie_msgs

#endif  // GENIE_MSGS__SRV__DETAIL__END_CAL__BUILDER_HPP_
