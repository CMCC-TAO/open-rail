// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from genie_msgs:msg/FaultStatus.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FAULT_STATUS__STRUCT_HPP_
#define GENIE_MSGS__MSG__DETAIL__FAULT_STATUS__STRUCT_HPP_

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
// Member 'faults'
#include "genie_msgs/msg/detail/fault_description__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__genie_msgs__msg__FaultStatus __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__msg__FaultStatus __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct FaultStatus_
{
  using Type = FaultStatus_<ContainerAllocator>;

  explicit FaultStatus_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    (void)_init;
  }

  explicit FaultStatus_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init)
  {
    (void)_init;
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _faults_type =
    std::vector<genie_msgs::msg::FaultDescription_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<genie_msgs::msg::FaultDescription_<ContainerAllocator>>>;
  _faults_type faults;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__faults(
    const std::vector<genie_msgs::msg::FaultDescription_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<genie_msgs::msg::FaultDescription_<ContainerAllocator>>> & _arg)
  {
    this->faults = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::msg::FaultStatus_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::msg::FaultStatus_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::msg::FaultStatus_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::msg::FaultStatus_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::FaultStatus_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::FaultStatus_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::FaultStatus_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::FaultStatus_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::msg::FaultStatus_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::msg::FaultStatus_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__msg__FaultStatus
    std::shared_ptr<genie_msgs::msg::FaultStatus_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__msg__FaultStatus
    std::shared_ptr<genie_msgs::msg::FaultStatus_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const FaultStatus_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->faults != other.faults) {
      return false;
    }
    return true;
  }
  bool operator!=(const FaultStatus_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct FaultStatus_

// alias to use template instance with default allocator
using FaultStatus =
  genie_msgs::msg::FaultStatus_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__FAULT_STATUS__STRUCT_HPP_
