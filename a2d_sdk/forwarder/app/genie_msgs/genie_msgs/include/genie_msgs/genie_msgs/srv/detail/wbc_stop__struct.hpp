// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from genie_msgs:srv/WbcStop.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__WBC_STOP__STRUCT_HPP_
#define GENIE_MSGS__SRV__DETAIL__WBC_STOP__STRUCT_HPP_

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
# define DEPRECATED__genie_msgs__srv__WbcStop_Request __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__srv__WbcStop_Request __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct WbcStop_Request_
{
  using Type = WbcStop_Request_<ContainerAllocator>;

  explicit WbcStop_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    (void)_init;
  }

  explicit WbcStop_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init)
  {
    (void)_init;
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::srv::WbcStop_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::srv::WbcStop_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::srv::WbcStop_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::srv::WbcStop_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::srv::WbcStop_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::srv::WbcStop_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::srv::WbcStop_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::srv::WbcStop_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::srv::WbcStop_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::srv::WbcStop_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__srv__WbcStop_Request
    std::shared_ptr<genie_msgs::srv::WbcStop_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__srv__WbcStop_Request
    std::shared_ptr<genie_msgs::srv::WbcStop_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const WbcStop_Request_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    return true;
  }
  bool operator!=(const WbcStop_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct WbcStop_Request_

// alias to use template instance with default allocator
using WbcStop_Request =
  genie_msgs::srv::WbcStop_Request_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace genie_msgs


// Include directives for member types
// Member 'res_header'
// already included above
// #include "std_msgs/msg/detail/header__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__genie_msgs__srv__WbcStop_Response __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__srv__WbcStop_Response __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct WbcStop_Response_
{
  using Type = WbcStop_Response_<ContainerAllocator>;

  explicit WbcStop_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : res_header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->stop_flag = false;
    }
  }

  explicit WbcStop_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : res_header(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->stop_flag = false;
    }
  }

  // field types and members
  using _res_header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _res_header_type res_header;
  using _stop_flag_type =
    bool;
  _stop_flag_type stop_flag;

  // setters for named parameter idiom
  Type & set__res_header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->res_header = _arg;
    return *this;
  }
  Type & set__stop_flag(
    const bool & _arg)
  {
    this->stop_flag = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::srv::WbcStop_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::srv::WbcStop_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::srv::WbcStop_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::srv::WbcStop_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::srv::WbcStop_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::srv::WbcStop_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::srv::WbcStop_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::srv::WbcStop_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::srv::WbcStop_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::srv::WbcStop_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__srv__WbcStop_Response
    std::shared_ptr<genie_msgs::srv::WbcStop_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__srv__WbcStop_Response
    std::shared_ptr<genie_msgs::srv::WbcStop_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const WbcStop_Response_ & other) const
  {
    if (this->res_header != other.res_header) {
      return false;
    }
    if (this->stop_flag != other.stop_flag) {
      return false;
    }
    return true;
  }
  bool operator!=(const WbcStop_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct WbcStop_Response_

// alias to use template instance with default allocator
using WbcStop_Response =
  genie_msgs::srv::WbcStop_Response_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace genie_msgs

namespace genie_msgs
{

namespace srv
{

struct WbcStop
{
  using Request = genie_msgs::srv::WbcStop_Request;
  using Response = genie_msgs::srv::WbcStop_Response;
};

}  // namespace srv

}  // namespace genie_msgs

#endif  // GENIE_MSGS__SRV__DETAIL__WBC_STOP__STRUCT_HPP_
