// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from genie_msgs:srv/AGVCancelTask.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__AGV_CANCEL_TASK__STRUCT_HPP_
#define GENIE_MSGS__SRV__DETAIL__AGV_CANCEL_TASK__STRUCT_HPP_

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
# define DEPRECATED__genie_msgs__srv__AGVCancelTask_Request __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__srv__AGVCancelTask_Request __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct AGVCancelTask_Request_
{
  using Type = AGVCancelTask_Request_<ContainerAllocator>;

  explicit AGVCancelTask_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->task_uuid = "";
    }
  }

  explicit AGVCancelTask_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init),
    task_uuid(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->task_uuid = "";
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _task_uuid_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _task_uuid_type task_uuid;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__task_uuid(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->task_uuid = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::srv::AGVCancelTask_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::srv::AGVCancelTask_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::srv::AGVCancelTask_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::srv::AGVCancelTask_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::srv::AGVCancelTask_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::srv::AGVCancelTask_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::srv::AGVCancelTask_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::srv::AGVCancelTask_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::srv::AGVCancelTask_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::srv::AGVCancelTask_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__srv__AGVCancelTask_Request
    std::shared_ptr<genie_msgs::srv::AGVCancelTask_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__srv__AGVCancelTask_Request
    std::shared_ptr<genie_msgs::srv::AGVCancelTask_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const AGVCancelTask_Request_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->task_uuid != other.task_uuid) {
      return false;
    }
    return true;
  }
  bool operator!=(const AGVCancelTask_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct AGVCancelTask_Request_

// alias to use template instance with default allocator
using AGVCancelTask_Request =
  genie_msgs::srv::AGVCancelTask_Request_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace genie_msgs


// Include directives for member types
// Member 'res_header'
// already included above
// #include "std_msgs/msg/detail/header__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__genie_msgs__srv__AGVCancelTask_Response __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__srv__AGVCancelTask_Response __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct AGVCancelTask_Response_
{
  using Type = AGVCancelTask_Response_<ContainerAllocator>;

  explicit AGVCancelTask_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : res_header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->req_result = 0ul;
      this->ret_code = 0ul;
      this->task_uuid = 0ul;
    }
  }

  explicit AGVCancelTask_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : res_header(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->req_result = 0ul;
      this->ret_code = 0ul;
      this->task_uuid = 0ul;
    }
  }

  // field types and members
  using _res_header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _res_header_type res_header;
  using _req_result_type =
    uint32_t;
  _req_result_type req_result;
  using _ret_code_type =
    uint32_t;
  _ret_code_type ret_code;
  using _task_uuid_type =
    uint32_t;
  _task_uuid_type task_uuid;

  // setters for named parameter idiom
  Type & set__res_header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->res_header = _arg;
    return *this;
  }
  Type & set__req_result(
    const uint32_t & _arg)
  {
    this->req_result = _arg;
    return *this;
  }
  Type & set__ret_code(
    const uint32_t & _arg)
  {
    this->ret_code = _arg;
    return *this;
  }
  Type & set__task_uuid(
    const uint32_t & _arg)
  {
    this->task_uuid = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::srv::AGVCancelTask_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::srv::AGVCancelTask_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::srv::AGVCancelTask_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::srv::AGVCancelTask_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::srv::AGVCancelTask_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::srv::AGVCancelTask_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::srv::AGVCancelTask_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::srv::AGVCancelTask_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::srv::AGVCancelTask_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::srv::AGVCancelTask_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__srv__AGVCancelTask_Response
    std::shared_ptr<genie_msgs::srv::AGVCancelTask_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__srv__AGVCancelTask_Response
    std::shared_ptr<genie_msgs::srv::AGVCancelTask_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const AGVCancelTask_Response_ & other) const
  {
    if (this->res_header != other.res_header) {
      return false;
    }
    if (this->req_result != other.req_result) {
      return false;
    }
    if (this->ret_code != other.ret_code) {
      return false;
    }
    if (this->task_uuid != other.task_uuid) {
      return false;
    }
    return true;
  }
  bool operator!=(const AGVCancelTask_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct AGVCancelTask_Response_

// alias to use template instance with default allocator
using AGVCancelTask_Response =
  genie_msgs::srv::AGVCancelTask_Response_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace genie_msgs

namespace genie_msgs
{

namespace srv
{

struct AGVCancelTask
{
  using Request = genie_msgs::srv::AGVCancelTask_Request;
  using Response = genie_msgs::srv::AGVCancelTask_Response;
};

}  // namespace srv

}  // namespace genie_msgs

#endif  // GENIE_MSGS__SRV__DETAIL__AGV_CANCEL_TASK__STRUCT_HPP_
