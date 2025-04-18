// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from genie_msgs:msg/EndState.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__END_STATE__STRUCT_HPP_
#define GENIE_MSGS__MSG__DETAIL__END_STATE__STRUCT_HPP_

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
// Member 'end_state'
#include "genie_msgs/msg/detail/motor_state__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__genie_msgs__msg__EndState __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__msg__EndState __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct EndState_
{
  using Type = EndState_<ContainerAllocator>;

  explicit EndState_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->controlled = false;
    }
  }

  explicit EndState_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->controlled = false;
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _controlled_type =
    bool;
  _controlled_type controlled;
  using _end_state_type =
    std::vector<genie_msgs::msg::MotorState_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<genie_msgs::msg::MotorState_<ContainerAllocator>>>;
  _end_state_type end_state;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__controlled(
    const bool & _arg)
  {
    this->controlled = _arg;
    return *this;
  }
  Type & set__end_state(
    const std::vector<genie_msgs::msg::MotorState_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<genie_msgs::msg::MotorState_<ContainerAllocator>>> & _arg)
  {
    this->end_state = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::msg::EndState_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::msg::EndState_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::msg::EndState_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::msg::EndState_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::EndState_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::EndState_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::EndState_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::EndState_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::msg::EndState_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::msg::EndState_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__msg__EndState
    std::shared_ptr<genie_msgs::msg::EndState_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__msg__EndState
    std::shared_ptr<genie_msgs::msg::EndState_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const EndState_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->controlled != other.controlled) {
      return false;
    }
    if (this->end_state != other.end_state) {
      return false;
    }
    return true;
  }
  bool operator!=(const EndState_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct EndState_

// alias to use template instance with default allocator
using EndState =
  genie_msgs::msg::EndState_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__END_STATE__STRUCT_HPP_
