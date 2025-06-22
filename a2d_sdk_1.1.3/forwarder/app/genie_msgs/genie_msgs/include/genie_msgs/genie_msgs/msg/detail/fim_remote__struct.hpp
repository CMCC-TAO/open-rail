// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from genie_msgs:msg/FimRemote.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FIM_REMOTE__STRUCT_HPP_
#define GENIE_MSGS__MSG__DETAIL__FIM_REMOTE__STRUCT_HPP_

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
# define DEPRECATED__genie_msgs__msg__FimRemote __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__msg__FimRemote __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct FimRemote_
{
  using Type = FimRemote_<ContainerAllocator>;

  explicit FimRemote_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->fim_vr = 0;
      this->vr_err_code = 0;
      this->fim_mocap = 0;
      this->mocap_err_code = 0;
    }
  }

  explicit FimRemote_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->fim_vr = 0;
      this->vr_err_code = 0;
      this->fim_mocap = 0;
      this->mocap_err_code = 0;
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _fim_vr_type =
    uint8_t;
  _fim_vr_type fim_vr;
  using _vr_err_code_type =
    uint16_t;
  _vr_err_code_type vr_err_code;
  using _fim_mocap_type =
    uint8_t;
  _fim_mocap_type fim_mocap;
  using _mocap_err_code_type =
    uint16_t;
  _mocap_err_code_type mocap_err_code;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__fim_vr(
    const uint8_t & _arg)
  {
    this->fim_vr = _arg;
    return *this;
  }
  Type & set__vr_err_code(
    const uint16_t & _arg)
  {
    this->vr_err_code = _arg;
    return *this;
  }
  Type & set__fim_mocap(
    const uint8_t & _arg)
  {
    this->fim_mocap = _arg;
    return *this;
  }
  Type & set__mocap_err_code(
    const uint16_t & _arg)
  {
    this->mocap_err_code = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::msg::FimRemote_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::msg::FimRemote_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::msg::FimRemote_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::msg::FimRemote_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::FimRemote_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::FimRemote_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::FimRemote_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::FimRemote_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::msg::FimRemote_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::msg::FimRemote_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__msg__FimRemote
    std::shared_ptr<genie_msgs::msg::FimRemote_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__msg__FimRemote
    std::shared_ptr<genie_msgs::msg::FimRemote_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const FimRemote_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->fim_vr != other.fim_vr) {
      return false;
    }
    if (this->vr_err_code != other.vr_err_code) {
      return false;
    }
    if (this->fim_mocap != other.fim_mocap) {
      return false;
    }
    if (this->mocap_err_code != other.mocap_err_code) {
      return false;
    }
    return true;
  }
  bool operator!=(const FimRemote_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct FimRemote_

// alias to use template instance with default allocator
using FimRemote =
  genie_msgs::msg::FimRemote_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__FIM_REMOTE__STRUCT_HPP_
