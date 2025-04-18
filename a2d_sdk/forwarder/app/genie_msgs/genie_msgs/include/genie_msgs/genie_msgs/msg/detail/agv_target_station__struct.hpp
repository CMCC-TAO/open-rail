// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from genie_msgs:msg/AGVTargetStation.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__AGV_TARGET_STATION__STRUCT_HPP_
#define GENIE_MSGS__MSG__DETAIL__AGV_TARGET_STATION__STRUCT_HPP_

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
# define DEPRECATED__genie_msgs__msg__AGVTargetStation __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__msg__AGVTargetStation __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct AGVTargetStation_
{
  using Type = AGVTargetStation_<ContainerAllocator>;

  explicit AGVTargetStation_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->station_id = 0ul;
      this->station_name = "";
      this->station_action = 0ul;
    }
  }

  explicit AGVTargetStation_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init),
    station_name(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->station_id = 0ul;
      this->station_name = "";
      this->station_action = 0ul;
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _station_id_type =
    uint32_t;
  _station_id_type station_id;
  using _station_name_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _station_name_type station_name;
  using _station_action_type =
    uint32_t;
  _station_action_type station_action;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__station_id(
    const uint32_t & _arg)
  {
    this->station_id = _arg;
    return *this;
  }
  Type & set__station_name(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->station_name = _arg;
    return *this;
  }
  Type & set__station_action(
    const uint32_t & _arg)
  {
    this->station_action = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::msg::AGVTargetStation_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::msg::AGVTargetStation_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::msg::AGVTargetStation_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::msg::AGVTargetStation_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::AGVTargetStation_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::AGVTargetStation_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::AGVTargetStation_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::AGVTargetStation_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::msg::AGVTargetStation_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::msg::AGVTargetStation_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__msg__AGVTargetStation
    std::shared_ptr<genie_msgs::msg::AGVTargetStation_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__msg__AGVTargetStation
    std::shared_ptr<genie_msgs::msg::AGVTargetStation_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const AGVTargetStation_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->station_id != other.station_id) {
      return false;
    }
    if (this->station_name != other.station_name) {
      return false;
    }
    if (this->station_action != other.station_action) {
      return false;
    }
    return true;
  }
  bool operator!=(const AGVTargetStation_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct AGVTargetStation_

// alias to use template instance with default allocator
using AGVTargetStation =
  genie_msgs::msg::AGVTargetStation_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__AGV_TARGET_STATION__STRUCT_HPP_
