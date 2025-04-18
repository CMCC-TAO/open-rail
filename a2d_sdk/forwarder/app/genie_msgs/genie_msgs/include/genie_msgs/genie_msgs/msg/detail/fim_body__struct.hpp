// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from genie_msgs:msg/FimBody.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FIM_BODY__STRUCT_HPP_
#define GENIE_MSGS__MSG__DETAIL__FIM_BODY__STRUCT_HPP_

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
# define DEPRECATED__genie_msgs__msg__FimBody __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__msg__FimBody __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct FimBody_
{
  using Type = FimBody_<ContainerAllocator>;

  explicit FimBody_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->fim_waist = 0;
      this->waist_err_code = 0;
      this->fim_lift = 0;
      this->lift_err_code = 0;
    }
  }

  explicit FimBody_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->fim_waist = 0;
      this->waist_err_code = 0;
      this->fim_lift = 0;
      this->lift_err_code = 0;
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _fim_waist_type =
    uint8_t;
  _fim_waist_type fim_waist;
  using _waist_err_code_type =
    uint16_t;
  _waist_err_code_type waist_err_code;
  using _fim_lift_type =
    uint8_t;
  _fim_lift_type fim_lift;
  using _lift_err_code_type =
    uint16_t;
  _lift_err_code_type lift_err_code;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__fim_waist(
    const uint8_t & _arg)
  {
    this->fim_waist = _arg;
    return *this;
  }
  Type & set__waist_err_code(
    const uint16_t & _arg)
  {
    this->waist_err_code = _arg;
    return *this;
  }
  Type & set__fim_lift(
    const uint8_t & _arg)
  {
    this->fim_lift = _arg;
    return *this;
  }
  Type & set__lift_err_code(
    const uint16_t & _arg)
  {
    this->lift_err_code = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::msg::FimBody_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::msg::FimBody_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::msg::FimBody_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::msg::FimBody_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::FimBody_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::FimBody_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::FimBody_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::FimBody_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::msg::FimBody_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::msg::FimBody_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__msg__FimBody
    std::shared_ptr<genie_msgs::msg::FimBody_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__msg__FimBody
    std::shared_ptr<genie_msgs::msg::FimBody_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const FimBody_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->fim_waist != other.fim_waist) {
      return false;
    }
    if (this->waist_err_code != other.waist_err_code) {
      return false;
    }
    if (this->fim_lift != other.fim_lift) {
      return false;
    }
    if (this->lift_err_code != other.lift_err_code) {
      return false;
    }
    return true;
  }
  bool operator!=(const FimBody_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct FimBody_

// alias to use template instance with default allocator
using FimBody =
  genie_msgs::msg::FimBody_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__FIM_BODY__STRUCT_HPP_
