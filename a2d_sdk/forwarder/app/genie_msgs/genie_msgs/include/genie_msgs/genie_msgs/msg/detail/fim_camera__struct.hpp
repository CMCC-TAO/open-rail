// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from genie_msgs:msg/FimCamera.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__FIM_CAMERA__STRUCT_HPP_
#define GENIE_MSGS__MSG__DETAIL__FIM_CAMERA__STRUCT_HPP_

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
# define DEPRECATED__genie_msgs__msg__FimCamera __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__msg__FimCamera __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct FimCamera_
{
  using Type = FimCamera_<ContainerAllocator>;

  explicit FimCamera_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    (void)_init;
  }

  explicit FimCamera_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init)
  {
    (void)_init;
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _fim_camera_type =
    std::vector<uint8_t, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<uint8_t>>;
  _fim_camera_type fim_camera;
  using _camera_name_type =
    std::vector<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>>>;
  _camera_name_type camera_name;
  using _err_code_type =
    std::vector<uint16_t, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<uint16_t>>;
  _err_code_type err_code;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__fim_camera(
    const std::vector<uint8_t, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<uint8_t>> & _arg)
  {
    this->fim_camera = _arg;
    return *this;
  }
  Type & set__camera_name(
    const std::vector<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>>> & _arg)
  {
    this->camera_name = _arg;
    return *this;
  }
  Type & set__err_code(
    const std::vector<uint16_t, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<uint16_t>> & _arg)
  {
    this->err_code = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::msg::FimCamera_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::msg::FimCamera_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::msg::FimCamera_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::msg::FimCamera_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::FimCamera_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::FimCamera_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::FimCamera_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::FimCamera_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::msg::FimCamera_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::msg::FimCamera_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__msg__FimCamera
    std::shared_ptr<genie_msgs::msg::FimCamera_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__msg__FimCamera
    std::shared_ptr<genie_msgs::msg::FimCamera_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const FimCamera_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->fim_camera != other.fim_camera) {
      return false;
    }
    if (this->camera_name != other.camera_name) {
      return false;
    }
    if (this->err_code != other.err_code) {
      return false;
    }
    return true;
  }
  bool operator!=(const FimCamera_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct FimCamera_

// alias to use template instance with default allocator
using FimCamera =
  genie_msgs::msg::FimCamera_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__FIM_CAMERA__STRUCT_HPP_
