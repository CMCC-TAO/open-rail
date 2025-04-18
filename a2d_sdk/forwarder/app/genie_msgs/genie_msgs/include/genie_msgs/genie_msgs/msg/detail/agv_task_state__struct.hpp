// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from genie_msgs:msg/AGVTaskState.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__AGV_TASK_STATE__STRUCT_HPP_
#define GENIE_MSGS__MSG__DETAIL__AGV_TASK_STATE__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__genie_msgs__msg__AGVTaskState __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__msg__AGVTaskState __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct AGVTaskState_
{
  using Type = AGVTaskState_<ContainerAllocator>;

  explicit AGVTaskState_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->task_uuid = 0ul;
      this->task_reqid = "";
      this->curr_station_idx = 0l;
      this->finish_state = 0ul;
    }
  }

  explicit AGVTaskState_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init),
    task_reqid(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->task_uuid = 0ul;
      this->task_reqid = "";
      this->curr_station_idx = 0l;
      this->finish_state = 0ul;
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _task_uuid_type =
    uint32_t;
  _task_uuid_type task_uuid;
  using _task_reqid_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _task_reqid_type task_reqid;
  using _curr_station_idx_type =
    int32_t;
  _curr_station_idx_type curr_station_idx;
  using _finish_state_type =
    uint32_t;
  _finish_state_type finish_state;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__task_uuid(
    const uint32_t & _arg)
  {
    this->task_uuid = _arg;
    return *this;
  }
  Type & set__task_reqid(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->task_reqid = _arg;
    return *this;
  }
  Type & set__curr_station_idx(
    const int32_t & _arg)
  {
    this->curr_station_idx = _arg;
    return *this;
  }
  Type & set__finish_state(
    const uint32_t & _arg)
  {
    this->finish_state = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::msg::AGVTaskState_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::msg::AGVTaskState_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::msg::AGVTaskState_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::msg::AGVTaskState_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::AGVTaskState_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::AGVTaskState_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::AGVTaskState_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::AGVTaskState_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::msg::AGVTaskState_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::msg::AGVTaskState_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__msg__AGVTaskState
    std::shared_ptr<genie_msgs::msg::AGVTaskState_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__msg__AGVTaskState
    std::shared_ptr<genie_msgs::msg::AGVTaskState_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const AGVTaskState_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->task_uuid != other.task_uuid) {
      return false;
    }
    if (this->task_reqid != other.task_reqid) {
      return false;
    }
    if (this->curr_station_idx != other.curr_station_idx) {
      return false;
    }
    if (this->finish_state != other.finish_state) {
      return false;
    }
    return true;
  }
  bool operator!=(const AGVTaskState_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct AGVTaskState_

// alias to use template instance with default allocator
using AGVTaskState =
  genie_msgs::msg::AGVTaskState_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__AGV_TASK_STATE__STRUCT_HPP_
