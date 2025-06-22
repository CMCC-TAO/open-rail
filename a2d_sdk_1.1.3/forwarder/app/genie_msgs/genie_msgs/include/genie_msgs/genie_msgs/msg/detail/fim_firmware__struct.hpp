// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from genie_msgs:msg/FimFirmware.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FIM_FIRMWARE__STRUCT_HPP_
#define GENIE_MSGS__MSG__DETAIL__FIM_FIRMWARE__STRUCT_HPP_

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
# define DEPRECATED__genie_msgs__msg__FimFirmware __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__msg__FimFirmware __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct FimFirmware_
{
  using Type = FimFirmware_<ContainerAllocator>;

  explicit FimFirmware_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->fim_fw = 0;
      this->err_code_byte = 0ul;
    }
  }

  explicit FimFirmware_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->fim_fw = 0;
      this->err_code_byte = 0ul;
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _fim_fw_type =
    uint8_t;
  _fim_fw_type fim_fw;
  using _err_code_byte_type =
    uint32_t;
  _err_code_byte_type err_code_byte;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__fim_fw(
    const uint8_t & _arg)
  {
    this->fim_fw = _arg;
    return *this;
  }
  Type & set__err_code_byte(
    const uint32_t & _arg)
  {
    this->err_code_byte = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::msg::FimFirmware_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::msg::FimFirmware_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::msg::FimFirmware_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::msg::FimFirmware_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::FimFirmware_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::FimFirmware_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::FimFirmware_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::FimFirmware_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::msg::FimFirmware_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::msg::FimFirmware_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__msg__FimFirmware
    std::shared_ptr<genie_msgs::msg::FimFirmware_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__msg__FimFirmware
    std::shared_ptr<genie_msgs::msg::FimFirmware_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const FimFirmware_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->fim_fw != other.fim_fw) {
      return false;
    }
    if (this->err_code_byte != other.err_code_byte) {
      return false;
    }
    return true;
  }
  bool operator!=(const FimFirmware_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct FimFirmware_

// alias to use template instance with default allocator
using FimFirmware =
  genie_msgs::msg::FimFirmware_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__FIM_FIRMWARE__STRUCT_HPP_
