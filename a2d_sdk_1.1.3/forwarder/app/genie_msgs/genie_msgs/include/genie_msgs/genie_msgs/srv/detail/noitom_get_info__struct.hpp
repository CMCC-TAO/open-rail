// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from genie_msgs:srv/NoitomGetInfo.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__NOITOM_GET_INFO__STRUCT_HPP_
#define GENIE_MSGS__SRV__DETAIL__NOITOM_GET_INFO__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__genie_msgs__srv__NoitomGetInfo_Request __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__srv__NoitomGetInfo_Request __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct NoitomGetInfo_Request_
{
  using Type = NoitomGetInfo_Request_<ContainerAllocator>;

  explicit NoitomGetInfo_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->structure_needs_at_least_one_member = 0;
    }
  }

  explicit NoitomGetInfo_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->structure_needs_at_least_one_member = 0;
    }
  }

  // field types and members
  using _structure_needs_at_least_one_member_type =
    uint8_t;
  _structure_needs_at_least_one_member_type structure_needs_at_least_one_member;


  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::srv::NoitomGetInfo_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::srv::NoitomGetInfo_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::srv::NoitomGetInfo_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::srv::NoitomGetInfo_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::srv::NoitomGetInfo_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::srv::NoitomGetInfo_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::srv::NoitomGetInfo_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::srv::NoitomGetInfo_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::srv::NoitomGetInfo_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::srv::NoitomGetInfo_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__srv__NoitomGetInfo_Request
    std::shared_ptr<genie_msgs::srv::NoitomGetInfo_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__srv__NoitomGetInfo_Request
    std::shared_ptr<genie_msgs::srv::NoitomGetInfo_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const NoitomGetInfo_Request_ & other) const
  {
    if (this->structure_needs_at_least_one_member != other.structure_needs_at_least_one_member) {
      return false;
    }
    return true;
  }
  bool operator!=(const NoitomGetInfo_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct NoitomGetInfo_Request_

// alias to use template instance with default allocator
using NoitomGetInfo_Request =
  genie_msgs::srv::NoitomGetInfo_Request_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace genie_msgs


#ifndef _WIN32
# define DEPRECATED__genie_msgs__srv__NoitomGetInfo_Response __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__srv__NoitomGetInfo_Response __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct NoitomGetInfo_Response_
{
  using Type = NoitomGetInfo_Response_<ContainerAllocator>;

  explicit NoitomGetInfo_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->device_sn = "";
      this->software_version = "";
      this->hardware_date = "";
      this->default_ip = "";
      this->default_port = 0;
    }
  }

  explicit NoitomGetInfo_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : device_sn(_alloc),
    software_version(_alloc),
    hardware_date(_alloc),
    default_ip(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->device_sn = "";
      this->software_version = "";
      this->hardware_date = "";
      this->default_ip = "";
      this->default_port = 0;
    }
  }

  // field types and members
  using _device_sn_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _device_sn_type device_sn;
  using _software_version_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _software_version_type software_version;
  using _hardware_date_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _hardware_date_type hardware_date;
  using _default_ip_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _default_ip_type default_ip;
  using _default_port_type =
    uint16_t;
  _default_port_type default_port;

  // setters for named parameter idiom
  Type & set__device_sn(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->device_sn = _arg;
    return *this;
  }
  Type & set__software_version(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->software_version = _arg;
    return *this;
  }
  Type & set__hardware_date(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->hardware_date = _arg;
    return *this;
  }
  Type & set__default_ip(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->default_ip = _arg;
    return *this;
  }
  Type & set__default_port(
    const uint16_t & _arg)
  {
    this->default_port = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::srv::NoitomGetInfo_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::srv::NoitomGetInfo_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::srv::NoitomGetInfo_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::srv::NoitomGetInfo_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::srv::NoitomGetInfo_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::srv::NoitomGetInfo_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::srv::NoitomGetInfo_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::srv::NoitomGetInfo_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::srv::NoitomGetInfo_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::srv::NoitomGetInfo_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__srv__NoitomGetInfo_Response
    std::shared_ptr<genie_msgs::srv::NoitomGetInfo_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__srv__NoitomGetInfo_Response
    std::shared_ptr<genie_msgs::srv::NoitomGetInfo_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const NoitomGetInfo_Response_ & other) const
  {
    if (this->device_sn != other.device_sn) {
      return false;
    }
    if (this->software_version != other.software_version) {
      return false;
    }
    if (this->hardware_date != other.hardware_date) {
      return false;
    }
    if (this->default_ip != other.default_ip) {
      return false;
    }
    if (this->default_port != other.default_port) {
      return false;
    }
    return true;
  }
  bool operator!=(const NoitomGetInfo_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct NoitomGetInfo_Response_

// alias to use template instance with default allocator
using NoitomGetInfo_Response =
  genie_msgs::srv::NoitomGetInfo_Response_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace genie_msgs

namespace genie_msgs
{

namespace srv
{

struct NoitomGetInfo
{
  using Request = genie_msgs::srv::NoitomGetInfo_Request;
  using Response = genie_msgs::srv::NoitomGetInfo_Response;
};

}  // namespace srv

}  // namespace genie_msgs

#endif  // GENIE_MSGS__SRV__DETAIL__NOITOM_GET_INFO__STRUCT_HPP_
