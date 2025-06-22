// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from genie_msgs:msg/AGVDetect.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__AGV_DETECT__STRUCT_HPP_
#define GENIE_MSGS__MSG__DETAIL__AGV_DETECT__STRUCT_HPP_

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
# define DEPRECATED__genie_msgs__msg__AGVDetect __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__msg__AGVDetect __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct AGVDetect_
{
  using Type = AGVDetect_<ContainerAllocator>;

  explicit AGVDetect_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->status = 0l;
      this->err_code = 0ul;
      this->obs_valid = false;
      this->obs_conf = 0.0f;
    }
  }

  explicit AGVDetect_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->status = 0l;
      this->err_code = 0ul;
      this->obs_valid = false;
      this->obs_conf = 0.0f;
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _status_type =
    int32_t;
  _status_type status;
  using _err_code_type =
    uint32_t;
  _err_code_type err_code;
  using _obs_valid_type =
    bool;
  _obs_valid_type obs_valid;
  using _obs_conf_type =
    float;
  _obs_conf_type obs_conf;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__status(
    const int32_t & _arg)
  {
    this->status = _arg;
    return *this;
  }
  Type & set__err_code(
    const uint32_t & _arg)
  {
    this->err_code = _arg;
    return *this;
  }
  Type & set__obs_valid(
    const bool & _arg)
  {
    this->obs_valid = _arg;
    return *this;
  }
  Type & set__obs_conf(
    const float & _arg)
  {
    this->obs_conf = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::msg::AGVDetect_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::msg::AGVDetect_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::msg::AGVDetect_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::msg::AGVDetect_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::AGVDetect_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::AGVDetect_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::AGVDetect_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::AGVDetect_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::msg::AGVDetect_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::msg::AGVDetect_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__msg__AGVDetect
    std::shared_ptr<genie_msgs::msg::AGVDetect_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__msg__AGVDetect
    std::shared_ptr<genie_msgs::msg::AGVDetect_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const AGVDetect_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->status != other.status) {
      return false;
    }
    if (this->err_code != other.err_code) {
      return false;
    }
    if (this->obs_valid != other.obs_valid) {
      return false;
    }
    if (this->obs_conf != other.obs_conf) {
      return false;
    }
    return true;
  }
  bool operator!=(const AGVDetect_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct AGVDetect_

// alias to use template instance with default allocator
using AGVDetect =
  genie_msgs::msg::AGVDetect_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__AGV_DETECT__STRUCT_HPP_
