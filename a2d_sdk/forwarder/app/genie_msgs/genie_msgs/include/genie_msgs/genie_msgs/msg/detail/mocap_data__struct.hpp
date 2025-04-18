// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from genie_msgs:msg/MocapData.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__MOCAP_DATA__STRUCT_HPP_
#define GENIE_MSGS__MSG__DETAIL__MOCAP_DATA__STRUCT_HPP_

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
// Member 'mocap_joint_states'
#include "genie_msgs/msg/detail/mocap_joint_state__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__genie_msgs__msg__MocapData __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__msg__MocapData __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct MocapData_
{
  using Type = MocapData_<ContainerAllocator>;

  explicit MocapData_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->status = 0ul;
      this->err_code = 0ul;
    }
  }

  explicit MocapData_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->status = 0ul;
      this->err_code = 0ul;
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _status_type =
    uint32_t;
  _status_type status;
  using _err_code_type =
    uint32_t;
  _err_code_type err_code;
  using _mocap_joint_states_type =
    std::vector<genie_msgs::msg::MocapJointState_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<genie_msgs::msg::MocapJointState_<ContainerAllocator>>>;
  _mocap_joint_states_type mocap_joint_states;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__status(
    const uint32_t & _arg)
  {
    this->status = _arg;
    return *this;
  }
  Type & set__err_code(
    const uint32_t & _arg)
  {
    this->err_code = _arg;
    return *this;
  }
  Type & set__mocap_joint_states(
    const std::vector<genie_msgs::msg::MocapJointState_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<genie_msgs::msg::MocapJointState_<ContainerAllocator>>> & _arg)
  {
    this->mocap_joint_states = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::msg::MocapData_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::msg::MocapData_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::msg::MocapData_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::msg::MocapData_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::MocapData_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::MocapData_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::MocapData_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::MocapData_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::msg::MocapData_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::msg::MocapData_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__msg__MocapData
    std::shared_ptr<genie_msgs::msg::MocapData_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__msg__MocapData
    std::shared_ptr<genie_msgs::msg::MocapData_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const MocapData_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->status != other.status) {
      return false;
    }
    if (this->err_code != other.err_code) {
      return false;
    }
    if (this->mocap_joint_states != other.mocap_joint_states) {
      return false;
    }
    return true;
  }
  bool operator!=(const MocapData_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct MocapData_

// alias to use template instance with default allocator
using MocapData =
  genie_msgs::msg::MocapData_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__MOCAP_DATA__STRUCT_HPP_
