// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from genie_msgs:msg/VRData.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__VR_DATA__STRUCT_HPP_
#define GENIE_MSGS__MSG__DETAIL__VR_DATA__STRUCT_HPP_

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
// Member 'vr_controller_states'
#include "genie_msgs/msg/detail/vr_controller_state__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__genie_msgs__msg__VRData __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__msg__VRData __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct VRData_
{
  using Type = VRData_<ContainerAllocator>;

  explicit VRData_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->status = 0ul;
      this->err_code = 0ul;
    }
  }

  explicit VRData_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
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
  using _vr_controller_states_type =
    std::vector<genie_msgs::msg::VRControllerState_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<genie_msgs::msg::VRControllerState_<ContainerAllocator>>>;
  _vr_controller_states_type vr_controller_states;

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
  Type & set__vr_controller_states(
    const std::vector<genie_msgs::msg::VRControllerState_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<genie_msgs::msg::VRControllerState_<ContainerAllocator>>> & _arg)
  {
    this->vr_controller_states = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::msg::VRData_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::msg::VRData_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::msg::VRData_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::msg::VRData_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::VRData_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::VRData_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::VRData_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::VRData_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::msg::VRData_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::msg::VRData_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__msg__VRData
    std::shared_ptr<genie_msgs::msg::VRData_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__msg__VRData
    std::shared_ptr<genie_msgs::msg::VRData_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const VRData_ & other) const
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
    if (this->vr_controller_states != other.vr_controller_states) {
      return false;
    }
    return true;
  }
  bool operator!=(const VRData_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct VRData_

// alias to use template instance with default allocator
using VRData =
  genie_msgs::msg::VRData_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__VR_DATA__STRUCT_HPP_
