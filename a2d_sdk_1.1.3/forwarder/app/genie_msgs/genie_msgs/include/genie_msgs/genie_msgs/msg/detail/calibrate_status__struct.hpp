// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from genie_msgs:msg/CalibrateStatus.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__CALIBRATE_STATUS__STRUCT_HPP_
#define GENIE_MSGS__MSG__DETAIL__CALIBRATE_STATUS__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__genie_msgs__msg__CalibrateStatus __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__msg__CalibrateStatus __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct CalibrateStatus_
{
  using Type = CalibrateStatus_<ContainerAllocator>;

  explicit CalibrateStatus_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->structure_needs_at_least_one_member = 0;
    }
  }

  explicit CalibrateStatus_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->structure_needs_at_least_one_member = 0;
    }
  }

  // field types and members
  using _structure_needs_at_least_one_member_type =
    uint8_t;
  _structure_needs_at_least_one_member_type structure_needs_at_least_one_member;


  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::msg::CalibrateStatus_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::msg::CalibrateStatus_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::msg::CalibrateStatus_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::msg::CalibrateStatus_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::CalibrateStatus_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::CalibrateStatus_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::CalibrateStatus_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::CalibrateStatus_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::msg::CalibrateStatus_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::msg::CalibrateStatus_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__msg__CalibrateStatus
    std::shared_ptr<genie_msgs::msg::CalibrateStatus_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__msg__CalibrateStatus
    std::shared_ptr<genie_msgs::msg::CalibrateStatus_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const CalibrateStatus_ & other) const
  {
    if (this->structure_needs_at_least_one_member != other.structure_needs_at_least_one_member) {
      return false;
    }
    return true;
  }
  bool operator!=(const CalibrateStatus_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct CalibrateStatus_

// alias to use template instance with default allocator
using CalibrateStatus =
  genie_msgs::msg::CalibrateStatus_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__CALIBRATE_STATUS__STRUCT_HPP_
