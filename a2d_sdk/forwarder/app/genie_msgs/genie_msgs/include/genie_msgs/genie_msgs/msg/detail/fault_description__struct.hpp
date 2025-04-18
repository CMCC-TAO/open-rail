// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from genie_msgs:msg/FaultDescription.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FAULT_DESCRIPTION__STRUCT_HPP_
#define GENIE_MSGS__MSG__DETAIL__FAULT_DESCRIPTION__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__genie_msgs__msg__FaultDescription __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__msg__FaultDescription __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct FaultDescription_
{
  using Type = FaultDescription_<ContainerAllocator>;

  explicit FaultDescription_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->error_id = "";
      this->error_code = 0;
    }
  }

  explicit FaultDescription_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : error_id(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->error_id = "";
      this->error_code = 0;
    }
  }

  // field types and members
  using _error_id_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _error_id_type error_id;
  using _error_code_type =
    uint16_t;
  _error_code_type error_code;

  // setters for named parameter idiom
  Type & set__error_id(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->error_id = _arg;
    return *this;
  }
  Type & set__error_code(
    const uint16_t & _arg)
  {
    this->error_code = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::msg::FaultDescription_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::msg::FaultDescription_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::msg::FaultDescription_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::msg::FaultDescription_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::FaultDescription_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::FaultDescription_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::FaultDescription_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::FaultDescription_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::msg::FaultDescription_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::msg::FaultDescription_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__msg__FaultDescription
    std::shared_ptr<genie_msgs::msg::FaultDescription_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__msg__FaultDescription
    std::shared_ptr<genie_msgs::msg::FaultDescription_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const FaultDescription_ & other) const
  {
    if (this->error_id != other.error_id) {
      return false;
    }
    if (this->error_code != other.error_code) {
      return false;
    }
    return true;
  }
  bool operator!=(const FaultDescription_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct FaultDescription_

// alias to use template instance with default allocator
using FaultDescription =
  genie_msgs::msg::FaultDescription_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__FAULT_DESCRIPTION__STRUCT_HPP_
