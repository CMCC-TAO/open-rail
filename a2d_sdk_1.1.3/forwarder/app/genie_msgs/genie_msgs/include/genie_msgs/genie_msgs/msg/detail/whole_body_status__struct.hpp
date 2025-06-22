// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from genie_msgs:msg/WholeBodyStatus.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__WHOLE_BODY_STATUS__STRUCT_HPP_
#define GENIE_MSGS__MSG__DETAIL__WHOLE_BODY_STATUS__STRUCT_HPP_

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
# define DEPRECATED__genie_msgs__msg__WholeBodyStatus __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__msg__WholeBodyStatus __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct WholeBodyStatus_
{
  using Type = WholeBodyStatus_<ContainerAllocator>;

  explicit WholeBodyStatus_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->right_arm_error = 0ul;
      this->left_arm_error = 0ul;
      this->right_arm_control = false;
      this->left_arm_control = false;
      this->right_arm_estop = false;
      this->left_arm_estop = false;
      this->right_end_error = 0ul;
      this->left_end_error = 0ul;
      this->waist_error = 0ul;
      this->lift_error = 0ul;
      this->neck_error = 0ul;
      this->chassis_error = 0ul;
    }
  }

  explicit WholeBodyStatus_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->right_arm_error = 0ul;
      this->left_arm_error = 0ul;
      this->right_arm_control = false;
      this->left_arm_control = false;
      this->right_arm_estop = false;
      this->left_arm_estop = false;
      this->right_end_error = 0ul;
      this->left_end_error = 0ul;
      this->waist_error = 0ul;
      this->lift_error = 0ul;
      this->neck_error = 0ul;
      this->chassis_error = 0ul;
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _right_arm_error_type =
    uint32_t;
  _right_arm_error_type right_arm_error;
  using _left_arm_error_type =
    uint32_t;
  _left_arm_error_type left_arm_error;
  using _right_arm_control_type =
    bool;
  _right_arm_control_type right_arm_control;
  using _left_arm_control_type =
    bool;
  _left_arm_control_type left_arm_control;
  using _right_arm_estop_type =
    bool;
  _right_arm_estop_type right_arm_estop;
  using _left_arm_estop_type =
    bool;
  _left_arm_estop_type left_arm_estop;
  using _right_end_error_type =
    uint32_t;
  _right_end_error_type right_end_error;
  using _left_end_error_type =
    uint32_t;
  _left_end_error_type left_end_error;
  using _waist_error_type =
    uint32_t;
  _waist_error_type waist_error;
  using _lift_error_type =
    uint32_t;
  _lift_error_type lift_error;
  using _neck_error_type =
    uint32_t;
  _neck_error_type neck_error;
  using _chassis_error_type =
    uint32_t;
  _chassis_error_type chassis_error;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__right_arm_error(
    const uint32_t & _arg)
  {
    this->right_arm_error = _arg;
    return *this;
  }
  Type & set__left_arm_error(
    const uint32_t & _arg)
  {
    this->left_arm_error = _arg;
    return *this;
  }
  Type & set__right_arm_control(
    const bool & _arg)
  {
    this->right_arm_control = _arg;
    return *this;
  }
  Type & set__left_arm_control(
    const bool & _arg)
  {
    this->left_arm_control = _arg;
    return *this;
  }
  Type & set__right_arm_estop(
    const bool & _arg)
  {
    this->right_arm_estop = _arg;
    return *this;
  }
  Type & set__left_arm_estop(
    const bool & _arg)
  {
    this->left_arm_estop = _arg;
    return *this;
  }
  Type & set__right_end_error(
    const uint32_t & _arg)
  {
    this->right_end_error = _arg;
    return *this;
  }
  Type & set__left_end_error(
    const uint32_t & _arg)
  {
    this->left_end_error = _arg;
    return *this;
  }
  Type & set__waist_error(
    const uint32_t & _arg)
  {
    this->waist_error = _arg;
    return *this;
  }
  Type & set__lift_error(
    const uint32_t & _arg)
  {
    this->lift_error = _arg;
    return *this;
  }
  Type & set__neck_error(
    const uint32_t & _arg)
  {
    this->neck_error = _arg;
    return *this;
  }
  Type & set__chassis_error(
    const uint32_t & _arg)
  {
    this->chassis_error = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::msg::WholeBodyStatus_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::msg::WholeBodyStatus_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::msg::WholeBodyStatus_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::msg::WholeBodyStatus_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::WholeBodyStatus_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::WholeBodyStatus_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::WholeBodyStatus_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::WholeBodyStatus_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::msg::WholeBodyStatus_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::msg::WholeBodyStatus_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__msg__WholeBodyStatus
    std::shared_ptr<genie_msgs::msg::WholeBodyStatus_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__msg__WholeBodyStatus
    std::shared_ptr<genie_msgs::msg::WholeBodyStatus_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const WholeBodyStatus_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->right_arm_error != other.right_arm_error) {
      return false;
    }
    if (this->left_arm_error != other.left_arm_error) {
      return false;
    }
    if (this->right_arm_control != other.right_arm_control) {
      return false;
    }
    if (this->left_arm_control != other.left_arm_control) {
      return false;
    }
    if (this->right_arm_estop != other.right_arm_estop) {
      return false;
    }
    if (this->left_arm_estop != other.left_arm_estop) {
      return false;
    }
    if (this->right_end_error != other.right_end_error) {
      return false;
    }
    if (this->left_end_error != other.left_end_error) {
      return false;
    }
    if (this->waist_error != other.waist_error) {
      return false;
    }
    if (this->lift_error != other.lift_error) {
      return false;
    }
    if (this->neck_error != other.neck_error) {
      return false;
    }
    if (this->chassis_error != other.chassis_error) {
      return false;
    }
    return true;
  }
  bool operator!=(const WholeBodyStatus_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct WholeBodyStatus_

// alias to use template instance with default allocator
using WholeBodyStatus =
  genie_msgs::msg::WholeBodyStatus_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__WHOLE_BODY_STATUS__STRUCT_HPP_
