// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from genie_msgs:msg/FeatureStatus.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FEATURE_STATUS__STRUCT_HPP_
#define GENIE_MSGS__MSG__DETAIL__FEATURE_STATUS__STRUCT_HPP_

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
# define DEPRECATED__genie_msgs__msg__FeatureStatus __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__msg__FeatureStatus __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct FeatureStatus_
{
  using Type = FeatureStatus_<ContainerAllocator>;

  explicit FeatureStatus_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->work_mode = 0;
      this->feature_status = 0;
    }
  }

  explicit FeatureStatus_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->work_mode = 0;
      this->feature_status = 0;
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _work_mode_type =
    uint8_t;
  _work_mode_type work_mode;
  using _feature_status_type =
    uint8_t;
  _feature_status_type feature_status;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__work_mode(
    const uint8_t & _arg)
  {
    this->work_mode = _arg;
    return *this;
  }
  Type & set__feature_status(
    const uint8_t & _arg)
  {
    this->feature_status = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::msg::FeatureStatus_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::msg::FeatureStatus_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::msg::FeatureStatus_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::msg::FeatureStatus_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::FeatureStatus_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::FeatureStatus_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::FeatureStatus_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::FeatureStatus_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::msg::FeatureStatus_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::msg::FeatureStatus_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__msg__FeatureStatus
    std::shared_ptr<genie_msgs::msg::FeatureStatus_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__msg__FeatureStatus
    std::shared_ptr<genie_msgs::msg::FeatureStatus_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const FeatureStatus_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->work_mode != other.work_mode) {
      return false;
    }
    if (this->feature_status != other.feature_status) {
      return false;
    }
    return true;
  }
  bool operator!=(const FeatureStatus_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct FeatureStatus_

// alias to use template instance with default allocator
using FeatureStatus =
  genie_msgs::msg::FeatureStatus_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__FEATURE_STATUS__STRUCT_HPP_
