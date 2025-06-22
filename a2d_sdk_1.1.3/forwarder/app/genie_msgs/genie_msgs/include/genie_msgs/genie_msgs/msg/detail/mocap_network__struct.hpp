// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from genie_msgs:msg/MocapNetwork.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__MOCAP_NETWORK__STRUCT_HPP_
#define GENIE_MSGS__MSG__DETAIL__MOCAP_NETWORK__STRUCT_HPP_

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
# define DEPRECATED__genie_msgs__msg__MocapNetwork __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__msg__MocapNetwork __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct MocapNetwork_
{
  using Type = MocapNetwork_<ContainerAllocator>;

  explicit MocapNetwork_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->device_name = "";
      this->is_connected = false;
      this->packet_loss_rate = 0.0f;
      this->latency = 0.0f;
      this->frequency = 0.0f;
      this->ip_address = "";
      this->remote_ip_address = "";
    }
  }

  explicit MocapNetwork_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init),
    device_name(_alloc),
    ip_address(_alloc),
    remote_ip_address(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->device_name = "";
      this->is_connected = false;
      this->packet_loss_rate = 0.0f;
      this->latency = 0.0f;
      this->frequency = 0.0f;
      this->ip_address = "";
      this->remote_ip_address = "";
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _device_name_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _device_name_type device_name;
  using _is_connected_type =
    bool;
  _is_connected_type is_connected;
  using _packet_loss_rate_type =
    float;
  _packet_loss_rate_type packet_loss_rate;
  using _latency_type =
    float;
  _latency_type latency;
  using _frequency_type =
    float;
  _frequency_type frequency;
  using _ip_address_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _ip_address_type ip_address;
  using _remote_ip_address_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _remote_ip_address_type remote_ip_address;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__device_name(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->device_name = _arg;
    return *this;
  }
  Type & set__is_connected(
    const bool & _arg)
  {
    this->is_connected = _arg;
    return *this;
  }
  Type & set__packet_loss_rate(
    const float & _arg)
  {
    this->packet_loss_rate = _arg;
    return *this;
  }
  Type & set__latency(
    const float & _arg)
  {
    this->latency = _arg;
    return *this;
  }
  Type & set__frequency(
    const float & _arg)
  {
    this->frequency = _arg;
    return *this;
  }
  Type & set__ip_address(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->ip_address = _arg;
    return *this;
  }
  Type & set__remote_ip_address(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->remote_ip_address = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::msg::MocapNetwork_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::msg::MocapNetwork_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::msg::MocapNetwork_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::msg::MocapNetwork_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::MocapNetwork_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::MocapNetwork_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::MocapNetwork_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::MocapNetwork_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::msg::MocapNetwork_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::msg::MocapNetwork_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__msg__MocapNetwork
    std::shared_ptr<genie_msgs::msg::MocapNetwork_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__msg__MocapNetwork
    std::shared_ptr<genie_msgs::msg::MocapNetwork_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const MocapNetwork_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->device_name != other.device_name) {
      return false;
    }
    if (this->is_connected != other.is_connected) {
      return false;
    }
    if (this->packet_loss_rate != other.packet_loss_rate) {
      return false;
    }
    if (this->latency != other.latency) {
      return false;
    }
    if (this->frequency != other.frequency) {
      return false;
    }
    if (this->ip_address != other.ip_address) {
      return false;
    }
    if (this->remote_ip_address != other.remote_ip_address) {
      return false;
    }
    return true;
  }
  bool operator!=(const MocapNetwork_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct MocapNetwork_

// alias to use template instance with default allocator
using MocapNetwork =
  genie_msgs::msg::MocapNetwork_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__MOCAP_NETWORK__STRUCT_HPP_
