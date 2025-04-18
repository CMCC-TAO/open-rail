// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from genie_msgs:srv/BodyPose.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__BODY_POSE__STRUCT_HPP_
#define GENIE_MSGS__SRV__DETAIL__BODY_POSE__STRUCT_HPP_

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
# define DEPRECATED__genie_msgs__srv__BodyPose_Request __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__srv__BodyPose_Request __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct BodyPose_Request_
{
  using Type = BodyPose_Request_<ContainerAllocator>;

  explicit BodyPose_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->joint_flag = 0l;
      this->block = false;
    }
  }

  explicit BodyPose_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->joint_flag = 0l;
      this->block = false;
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _joint_flag_type =
    int32_t;
  _joint_flag_type joint_flag;
  using _joint_states_type =
    std::vector<float, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<float>>;
  _joint_states_type joint_states;
  using _block_type =
    bool;
  _block_type block;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__joint_flag(
    const int32_t & _arg)
  {
    this->joint_flag = _arg;
    return *this;
  }
  Type & set__joint_states(
    const std::vector<float, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<float>> & _arg)
  {
    this->joint_states = _arg;
    return *this;
  }
  Type & set__block(
    const bool & _arg)
  {
    this->block = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::srv::BodyPose_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::srv::BodyPose_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::srv::BodyPose_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::srv::BodyPose_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::srv::BodyPose_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::srv::BodyPose_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::srv::BodyPose_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::srv::BodyPose_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::srv::BodyPose_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::srv::BodyPose_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__srv__BodyPose_Request
    std::shared_ptr<genie_msgs::srv::BodyPose_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__srv__BodyPose_Request
    std::shared_ptr<genie_msgs::srv::BodyPose_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const BodyPose_Request_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->joint_flag != other.joint_flag) {
      return false;
    }
    if (this->joint_states != other.joint_states) {
      return false;
    }
    if (this->block != other.block) {
      return false;
    }
    return true;
  }
  bool operator!=(const BodyPose_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct BodyPose_Request_

// alias to use template instance with default allocator
using BodyPose_Request =
  genie_msgs::srv::BodyPose_Request_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace genie_msgs


// Include directives for member types
// Member 'res_header'
// already included above
// #include "std_msgs/msg/detail/header__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__genie_msgs__srv__BodyPose_Response __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__srv__BodyPose_Response __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct BodyPose_Response_
{
  using Type = BodyPose_Response_<ContainerAllocator>;

  explicit BodyPose_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : res_header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->exec_result = 0;
    }
  }

  explicit BodyPose_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
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
    genie_msgs::srv::BodyPose_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::srv::BodyPose_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::srv::BodyPose_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::srv::BodyPose_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::srv::BodyPose_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::srv::BodyPose_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::srv::BodyPose_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::srv::BodyPose_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::srv::BodyPose_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::srv::BodyPose_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__srv__BodyPose_Response
    std::shared_ptr<genie_msgs::srv::BodyPose_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__srv__BodyPose_Response
    std::shared_ptr<genie_msgs::srv::BodyPose_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const BodyPose_Response_ & other) const
  {
    if (this->res_header != other.res_header) {
      return false;
    }
    if (this->exec_result != other.exec_result) {
      return false;
    }
    return true;
  }
  bool operator!=(const BodyPose_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct BodyPose_Response_

// alias to use template instance with default allocator
using BodyPose_Response =
  genie_msgs::srv::BodyPose_Response_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace genie_msgs

namespace genie_msgs
{

namespace srv
{

struct BodyPose
{
  using Request = genie_msgs::srv::BodyPose_Request;
  using Response = genie_msgs::srv::BodyPose_Response;
};

}  // namespace srv

}  // namespace genie_msgs

#endif  // GENIE_MSGS__SRV__DETAIL__BODY_POSE__STRUCT_HPP_
