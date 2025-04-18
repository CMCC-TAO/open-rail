// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from genie_msgs:srv/NoitomSetFreq.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__SRV__DETAIL__NOITOM_SET_FREQ__STRUCT_HPP_
#define GENIE_MSGS__SRV__DETAIL__NOITOM_SET_FREQ__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__genie_msgs__srv__NoitomSetFreq_Request __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__srv__NoitomSetFreq_Request __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct NoitomSetFreq_Request_
{
  using Type = NoitomSetFreq_Request_<ContainerAllocator>;

  explicit NoitomSetFreq_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->frequency = 0.0f;
    }
  }

  explicit NoitomSetFreq_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->frequency = 0.0f;
    }
  }

  // field types and members
  using _frequency_type =
    float;
  _frequency_type frequency;

  // setters for named parameter idiom
  Type & set__frequency(
    const float & _arg)
  {
    this->frequency = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::srv::NoitomSetFreq_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::srv::NoitomSetFreq_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::srv::NoitomSetFreq_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::srv::NoitomSetFreq_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::srv::NoitomSetFreq_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::srv::NoitomSetFreq_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::srv::NoitomSetFreq_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::srv::NoitomSetFreq_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::srv::NoitomSetFreq_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::srv::NoitomSetFreq_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__srv__NoitomSetFreq_Request
    std::shared_ptr<genie_msgs::srv::NoitomSetFreq_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__srv__NoitomSetFreq_Request
    std::shared_ptr<genie_msgs::srv::NoitomSetFreq_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const NoitomSetFreq_Request_ & other) const
  {
    if (this->frequency != other.frequency) {
      return false;
    }
    return true;
  }
  bool operator!=(const NoitomSetFreq_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct NoitomSetFreq_Request_

// alias to use template instance with default allocator
using NoitomSetFreq_Request =
  genie_msgs::srv::NoitomSetFreq_Request_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace genie_msgs


#ifndef _WIN32
# define DEPRECATED__genie_msgs__srv__NoitomSetFreq_Response __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__srv__NoitomSetFreq_Response __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct NoitomSetFreq_Response_
{
  using Type = NoitomSetFreq_Response_<ContainerAllocator>;

  explicit NoitomSetFreq_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->success = false;
      this->current_frequency = 0.0f;
      this->message = "";
    }
  }

  explicit NoitomSetFreq_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : message(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->success = false;
      this->current_frequency = 0.0f;
      this->message = "";
    }
  }

  // field types and members
  using _success_type =
    bool;
  _success_type success;
  using _current_frequency_type =
    float;
  _current_frequency_type current_frequency;
  using _message_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _message_type message;

  // setters for named parameter idiom
  Type & set__success(
    const bool & _arg)
  {
    this->success = _arg;
    return *this;
  }
  Type & set__current_frequency(
    const float & _arg)
  {
    this->current_frequency = _arg;
    return *this;
  }
  Type & set__message(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->message = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::srv::NoitomSetFreq_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::srv::NoitomSetFreq_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::srv::NoitomSetFreq_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::srv::NoitomSetFreq_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::srv::NoitomSetFreq_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::srv::NoitomSetFreq_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::srv::NoitomSetFreq_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::srv::NoitomSetFreq_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::srv::NoitomSetFreq_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::srv::NoitomSetFreq_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__srv__NoitomSetFreq_Response
    std::shared_ptr<genie_msgs::srv::NoitomSetFreq_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__srv__NoitomSetFreq_Response
    std::shared_ptr<genie_msgs::srv::NoitomSetFreq_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const NoitomSetFreq_Response_ & other) const
  {
    if (this->success != other.success) {
      return false;
    }
    if (this->current_frequency != other.current_frequency) {
      return false;
    }
    if (this->message != other.message) {
      return false;
    }
    return true;
  }
  bool operator!=(const NoitomSetFreq_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct NoitomSetFreq_Response_

// alias to use template instance with default allocator
using NoitomSetFreq_Response =
  genie_msgs::srv::NoitomSetFreq_Response_<std::allocator<void>>;

// constant definitions

}  // namespace srv

}  // namespace genie_msgs

namespace genie_msgs
{

namespace srv
{

struct NoitomSetFreq
{
  using Request = genie_msgs::srv::NoitomSetFreq_Request;
  using Response = genie_msgs::srv::NoitomSetFreq_Response;
};

}  // namespace srv

}  // namespace genie_msgs

#endif  // GENIE_MSGS__SRV__DETAIL__NOITOM_SET_FREQ__STRUCT_HPP_
