// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from genie_msgs:srv/RecordControl.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__RECORD_CONTROL__STRUCT_HPP_
#define GENIE_MSGS__SRV__DETAIL__RECORD_CONTROL__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


// Include directives for member types
// Member 'req_header'
#include "std_msgs/msg/detail/header__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__genie_msgs__srv__RecordControl_Request __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__srv__RecordControl_Request __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct RecordControl_Request_
{
  using Type = RecordControl_Request_<ContainerAllocator>;

  explicit RecordControl_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : req_header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->record = false;
    }
  }

  explicit RecordControl_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : req_header(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->record = false;
    }
  }

  // field types and members
  using _req_header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _req_header_type req_header;
  using _record_type =
    bool;
  _record_type record;

  // setters for named parameter idiom
  Type & set__req_header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->req_header = _arg;
    return *this;
  }
  Type & set__record(
    const bool & _arg)
  {
    this->record = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::srv::RecordControl_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::srv::RecordControl_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::srv::RecordControl_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::srv::RecordControl_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::srv::RecordControl_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::srv::RecordControl_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::srv::RecordControl_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::srv::RecordControl_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::srv::RecordControl_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::srv::RecordControl_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__srv__RecordControl_Request
    std::shared_ptr<genie_msgs::srv::RecordControl_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__srv__RecordControl_Request
    std::shared_ptr<genie_msgs::srv::RecordControl_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const RecordControl_Request_ & other) const
  {
    if (this->req_header != other.req_header) {
      return false;
    }
    if (this->record != other.record) {
      return false;
    }
    return true;
  }
  bool operator!=(const RecordControl_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct RecordControl_Request_

// alias to use template instance with default allocator
using RecordControl_Request =
  genie_msgs::srv::RecordControl_Request_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace genie_msgs


// Include directives for member types
// Member 'res_header'
// already included above
// #include "std_msgs/msg/detail/header__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__genie_msgs__srv__RecordControl_Response __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__srv__RecordControl_Response __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct RecordControl_Response_
{
  using Type = RecordControl_Response_<ContainerAllocator>;

  explicit RecordControl_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : res_header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->exec_result = 0;
    }
  }

  explicit RecordControl_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : res_header(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->exec_result = 0;
    }
  }

  // field types and members
  using _res_header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _res_header_type res_header;
  using _exec_result_type =
    uint8_t;
  _exec_result_type exec_result;

  // setters for named parameter idiom
  Type & set__res_header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->res_header = _arg;
    return *this;
  }
  Type & set__exec_result(
    const uint8_t & _arg)
  {
    this->exec_result = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::srv::RecordControl_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::srv::RecordControl_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::srv::RecordControl_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::srv::RecordControl_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::srv::RecordControl_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::srv::RecordControl_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::srv::RecordControl_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::srv::RecordControl_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::srv::RecordControl_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::srv::RecordControl_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__srv__RecordControl_Response
    std::shared_ptr<genie_msgs::srv::RecordControl_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__srv__RecordControl_Response
    std::shared_ptr<genie_msgs::srv::RecordControl_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const RecordControl_Response_ & other) const
  {
    if (this->res_header != other.res_header) {
      return false;
    }
    if (this->exec_result != other.exec_result) {
      return false;
    }
    return true;
  }
  bool operator!=(const RecordControl_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct RecordControl_Response_

// alias to use template instance with default allocator
using RecordControl_Response =
  genie_msgs::srv::RecordControl_Response_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace genie_msgs

namespace genie_msgs
{

namespace srv
{

struct RecordControl
{
  using Request = genie_msgs::srv::RecordControl_Request;
  using Response = genie_msgs::srv::RecordControl_Response;
};

}  // namespace srv

}  // namespace genie_msgs

#endif  // GENIE_MSGS__SRV__DETAIL__RECORD_CONTROL__STRUCT_HPP_
