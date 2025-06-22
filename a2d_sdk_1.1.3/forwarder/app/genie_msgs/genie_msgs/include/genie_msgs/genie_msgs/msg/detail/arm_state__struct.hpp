// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from genie_msgs:msg/ArmState.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__ARM_STATE__STRUCT_HPP_
#define GENIE_MSGS__MSG__DETAIL__ARM_STATE__STRUCT_HPP_

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
// Member 'motor_states'
#include "genie_msgs/msg/detail/motor_state__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__genie_msgs__msg__ArmState __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__msg__ArmState __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct ArmState_
{
  using Type = ArmState_<ContainerAllocator>;

  explicit ArmState_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->force_coordinate = 0l;
      this->force_state = 0l;
      this->arm_state = 0ul;
      this->system_error = 0l;
    }
  }

  explicit ArmState_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->force_coordinate = 0l;
      this->force_state = 0l;
      this->arm_state = 0ul;
      this->system_error = 0l;
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _motor_states_type =
    std::vector<genie_msgs::msg::MotorState_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<genie_msgs::msg::MotorState_<ContainerAllocator>>>;
  _motor_states_type motor_states;
  using _force_data_type =
    std::vector<double, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<double>>;
  _force_data_type force_data;
  using _force_coordinate_type =
    int32_t;
  _force_coordinate_type force_coordinate;
  using _force_state_type =
    int32_t;
  _force_state_type force_state;
  using _arm_state_type =
    uint32_t;
  _arm_state_type arm_state;
  using _system_error_type =
    int32_t;
  _system_error_type system_error;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__motor_states(
    const std::vector<genie_msgs::msg::MotorState_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<genie_msgs::msg::MotorState_<ContainerAllocator>>> & _arg)
  {
    this->motor_states = _arg;
    return *this;
  }
  Type & set__force_data(
    const std::vector<double, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<double>> & _arg)
  {
    this->force_data = _arg;
    return *this;
  }
  Type & set__force_coordinate(
    const int32_t & _arg)
  {
    this->force_coordinate = _arg;
    return *this;
  }
  Type & set__force_state(
    const int32_t & _arg)
  {
    this->force_state = _arg;
    return *this;
  }
  Type & set__arm_state(
    const uint32_t & _arg)
  {
    this->arm_state = _arg;
    return *this;
  }
  Type & set__system_error(
    const int32_t & _arg)
  {
    this->system_error = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::msg::ArmState_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::msg::ArmState_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::msg::ArmState_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::msg::ArmState_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::ArmState_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::ArmState_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::ArmState_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::ArmState_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::msg::ArmState_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::msg::ArmState_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__msg__ArmState
    std::shared_ptr<genie_msgs::msg::ArmState_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__msg__ArmState
    std::shared_ptr<genie_msgs::msg::ArmState_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const ArmState_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->motor_states != other.motor_states) {
      return false;
    }
    if (this->force_data != other.force_data) {
      return false;
    }
    if (this->force_coordinate != other.force_coordinate) {
      return false;
    }
    if (this->force_state != other.force_state) {
      return false;
    }
    if (this->arm_state != other.arm_state) {
      return false;
    }
    if (this->system_error != other.system_error) {
      return false;
    }
    return true;
  }
  bool operator!=(const ArmState_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct ArmState_

// alias to use template instance with default allocator
using ArmState =
  genie_msgs::msg::ArmState_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__ARM_STATE__STRUCT_HPP_
