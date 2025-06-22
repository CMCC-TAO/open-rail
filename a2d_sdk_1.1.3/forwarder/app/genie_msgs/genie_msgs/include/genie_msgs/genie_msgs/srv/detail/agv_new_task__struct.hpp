// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from genie_msgs:srv/AGVNewTask.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__AGV_NEW_TASK__STRUCT_HPP_
#define GENIE_MSGS__SRV__DETAIL__AGV_NEW_TASK__STRUCT_HPP_

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
// Member 'target_station_list'
#include "genie_msgs/msg/detail/target_station__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__genie_msgs__srv__AGVNewTask_Request __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__srv__AGVNewTask_Request __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct AGVNewTask_Request_
{
  using Type = AGVNewTask_Request_<ContainerAllocator>;

  explicit AGVNewTask_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->task_reqid = "";
      this->map_id = 0ul;
      this->is_loop = false;
    }
  }

  explicit AGVNewTask_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init),
    task_reqid(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->task_reqid = "";
      this->map_id = 0ul;
      this->is_loop = false;
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _task_reqid_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _task_reqid_type task_reqid;
  using _map_id_type =
    uint32_t;
  _map_id_type map_id;
  using _target_station_list_type =
    std::vector<genie_msgs::msg::TargetStation_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<genie_msgs::msg::TargetStation_<ContainerAllocator>>>;
  _target_station_list_type target_station_list;
  using _is_loop_type =
    bool;
  _is_loop_type is_loop;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__task_reqid(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->task_reqid = _arg;
    return *this;
  }
  Type & set__map_id(
    const uint32_t & _arg)
  {
    this->map_id = _arg;
    return *this;
  }
  Type & set__target_station_list(
    const std::vector<genie_msgs::msg::TargetStation_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<genie_msgs::msg::TargetStation_<ContainerAllocator>>> & _arg)
  {
    this->target_station_list = _arg;
    return *this;
  }
  Type & set__is_loop(
    const bool & _arg)
  {
    this->is_loop = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::srv::AGVNewTask_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::srv::AGVNewTask_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::srv::AGVNewTask_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::srv::AGVNewTask_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::srv::AGVNewTask_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::srv::AGVNewTask_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::srv::AGVNewTask_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::srv::AGVNewTask_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::srv::AGVNewTask_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::srv::AGVNewTask_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__srv__AGVNewTask_Request
    std::shared_ptr<genie_msgs::srv::AGVNewTask_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__srv__AGVNewTask_Request
    std::shared_ptr<genie_msgs::srv::AGVNewTask_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const AGVNewTask_Request_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->task_reqid != other.task_reqid) {
      return false;
    }
    if (this->map_id != other.map_id) {
      return false;
    }
    if (this->target_station_list != other.target_station_list) {
      return false;
    }
    if (this->is_loop != other.is_loop) {
      return false;
    }
    return true;
  }
  bool operator!=(const AGVNewTask_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct AGVNewTask_Request_

// alias to use template instance with default allocator
using AGVNewTask_Request =
  genie_msgs::srv::AGVNewTask_Request_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace genie_msgs


// Include directives for member types
// Member 'res_header'
// already included above
// #include "std_msgs/msg/detail/header__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__genie_msgs__srv__AGVNewTask_Response __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__srv__AGVNewTask_Response __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct AGVNewTask_Response_
{
  using Type = AGVNewTask_Response_<ContainerAllocator>;

  explicit AGVNewTask_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : res_header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->req_result = 0ul;
      this->ret_code = 0ul;
      this->task_uuid = 0ul;
      this->task_reqid = "";
    }
  }

  explicit AGVNewTask_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : res_header(_alloc, _init),
    task_reqid(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->req_result = 0ul;
      this->ret_code = 0ul;
      this->task_uuid = 0ul;
      this->task_reqid = "";
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
  using _task_reqid_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _task_reqid_type task_reqid;

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
  Type & set__task_reqid(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->task_reqid = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::srv::AGVNewTask_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::srv::AGVNewTask_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::srv::AGVNewTask_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::srv::AGVNewTask_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::srv::AGVNewTask_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::srv::AGVNewTask_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::srv::AGVNewTask_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::srv::AGVNewTask_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::srv::AGVNewTask_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::srv::AGVNewTask_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__srv__AGVNewTask_Response
    std::shared_ptr<genie_msgs::srv::AGVNewTask_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__srv__AGVNewTask_Response
    std::shared_ptr<genie_msgs::srv::AGVNewTask_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const AGVNewTask_Response_ & other) const
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
    if (this->task_reqid != other.task_reqid) {
      return false;
    }
    return true;
  }
  bool operator!=(const AGVNewTask_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct AGVNewTask_Response_

// alias to use template instance with default allocator
using AGVNewTask_Response =
  genie_msgs::srv::AGVNewTask_Response_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace genie_msgs

namespace genie_msgs
{

namespace srv
{

struct AGVNewTask
{
  using Request = genie_msgs::srv::AGVNewTask_Request;
  using Response = genie_msgs::srv::AGVNewTask_Response;
};

}  // namespace srv

}  // namespace genie_msgs

#endif  // GENIE_MSGS__SRV__DETAIL__AGV_NEW_TASK__STRUCT_HPP_
