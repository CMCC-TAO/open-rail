// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from genie_msgs:msg/Retarget.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__RETARGET__STRUCT_HPP_
#define GENIE_MSGS__MSG__DETAIL__RETARGET__STRUCT_HPP_

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
// Member 'left_ee_pose'
// Member 'right_ee_pose'
// Member 'left_upper_arm'
// Member 'right_upper_arm'
#include "geometry_msgs/msg/detail/pose__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__genie_msgs__msg__Retarget __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__msg__Retarget __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct Retarget_
{
  using Type = Retarget_<ContainerAllocator>;

  explicit Retarget_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init),
    left_ee_pose(_init),
    right_ee_pose(_init),
    left_upper_arm(_init),
    right_upper_arm(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->group_arms = 0;
      this->group_body = 0;
      this->device = 0;
    }
  }

  explicit Retarget_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init),
    left_ee_pose(_alloc, _init),
    right_ee_pose(_alloc, _init),
    left_upper_arm(_alloc, _init),
    right_upper_arm(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->group_arms = 0;
      this->group_body = 0;
      this->device = 0;
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _group_arms_type =
    uint8_t;
  _group_arms_type group_arms;
  using _group_body_type =
    uint8_t;
  _group_body_type group_body;
  using _device_type =
    uint8_t;
  _device_type device;
  using _left_ee_pose_type =
    geometry_msgs::msg::Pose_<ContainerAllocator>;
  _left_ee_pose_type left_ee_pose;
  using _right_ee_pose_type =
    geometry_msgs::msg::Pose_<ContainerAllocator>;
  _right_ee_pose_type right_ee_pose;
  using _left_upper_arm_type =
    geometry_msgs::msg::Pose_<ContainerAllocator>;
  _left_upper_arm_type left_upper_arm;
  using _right_upper_arm_type =
    geometry_msgs::msg::Pose_<ContainerAllocator>;
  _right_upper_arm_type right_upper_arm;
  using _body_joint_names_type =
    std::vector<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>>>;
  _body_joint_names_type body_joint_names;
  using _body_joint_positions_type =
    std::vector<double, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<double>>;
  _body_joint_positions_type body_joint_positions;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__group_arms(
    const uint8_t & _arg)
  {
    this->group_arms = _arg;
    return *this;
  }
  Type & set__group_body(
    const uint8_t & _arg)
  {
    this->group_body = _arg;
    return *this;
  }
  Type & set__device(
    const uint8_t & _arg)
  {
    this->device = _arg;
    return *this;
  }
  Type & set__left_ee_pose(
    const geometry_msgs::msg::Pose_<ContainerAllocator> & _arg)
  {
    this->left_ee_pose = _arg;
    return *this;
  }
  Type & set__right_ee_pose(
    const geometry_msgs::msg::Pose_<ContainerAllocator> & _arg)
  {
    this->right_ee_pose = _arg;
    return *this;
  }
  Type & set__left_upper_arm(
    const geometry_msgs::msg::Pose_<ContainerAllocator> & _arg)
  {
    this->left_upper_arm = _arg;
    return *this;
  }
  Type & set__right_upper_arm(
    const geometry_msgs::msg::Pose_<ContainerAllocator> & _arg)
  {
    this->right_upper_arm = _arg;
    return *this;
  }
  Type & set__body_joint_names(
    const std::vector<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>>> & _arg)
  {
    this->body_joint_names = _arg;
    return *this;
  }
  Type & set__body_joint_positions(
    const std::vector<double, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<double>> & _arg)
  {
    this->body_joint_positions = _arg;
    return *this;
  }

  // constant declarations
  static constexpr uint8_t NONE =
    0u;
  static constexpr uint8_t DURAL_ARM =
    1u;
  static constexpr uint8_t LEFT_ARM =
    2u;
  static constexpr uint8_t RIGHT_ARM =
    3u;
  static constexpr uint8_t WAIST =
    4u;
  static constexpr uint8_t HEAD =
    5u;
  static constexpr uint8_t WAIST_HEAD =
    6u;
  static constexpr uint8_t VR =
    101u;
  static constexpr uint8_t MOCAP =
    102u;

  // pointer types
  using RawPtr =
    genie_msgs::msg::Retarget_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::msg::Retarget_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::msg::Retarget_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::msg::Retarget_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::Retarget_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::Retarget_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::Retarget_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::Retarget_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::msg::Retarget_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::msg::Retarget_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__msg__Retarget
    std::shared_ptr<genie_msgs::msg::Retarget_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__msg__Retarget
    std::shared_ptr<genie_msgs::msg::Retarget_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const Retarget_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->group_arms != other.group_arms) {
      return false;
    }
    if (this->group_body != other.group_body) {
      return false;
    }
    if (this->device != other.device) {
      return false;
    }
    if (this->left_ee_pose != other.left_ee_pose) {
      return false;
    }
    if (this->right_ee_pose != other.right_ee_pose) {
      return false;
    }
    if (this->left_upper_arm != other.left_upper_arm) {
      return false;
    }
    if (this->right_upper_arm != other.right_upper_arm) {
      return false;
    }
    if (this->body_joint_names != other.body_joint_names) {
      return false;
    }
    if (this->body_joint_positions != other.body_joint_positions) {
      return false;
    }
    return true;
  }
  bool operator!=(const Retarget_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct Retarget_

// alias to use template instance with default allocator
using Retarget =
  genie_msgs::msg::Retarget_<std::allocator<void>>;

// constant definitions
#if __cplusplus < 201703L
// static constexpr member variable definitions are only needed in C++14 and below, deprecated in C++17
template<typename ContainerAllocator>
constexpr uint8_t Retarget_<ContainerAllocator>::NONE;
#endif  // __cplusplus < 201703L
#if __cplusplus < 201703L
// static constexpr member variable definitions are only needed in C++14 and below, deprecated in C++17
template<typename ContainerAllocator>
constexpr uint8_t Retarget_<ContainerAllocator>::DURAL_ARM;
#endif  // __cplusplus < 201703L
#if __cplusplus < 201703L
// static constexpr member variable definitions are only needed in C++14 and below, deprecated in C++17
template<typename ContainerAllocator>
constexpr uint8_t Retarget_<ContainerAllocator>::LEFT_ARM;
#endif  // __cplusplus < 201703L
#if __cplusplus < 201703L
// static constexpr member variable definitions are only needed in C++14 and below, deprecated in C++17
template<typename ContainerAllocator>
constexpr uint8_t Retarget_<ContainerAllocator>::RIGHT_ARM;
#endif  // __cplusplus < 201703L
#if __cplusplus < 201703L
// static constexpr member variable definitions are only needed in C++14 and below, deprecated in C++17
template<typename ContainerAllocator>
constexpr uint8_t Retarget_<ContainerAllocator>::WAIST;
#endif  // __cplusplus < 201703L
#if __cplusplus < 201703L
// static constexpr member variable definitions are only needed in C++14 and below, deprecated in C++17
template<typename ContainerAllocator>
constexpr uint8_t Retarget_<ContainerAllocator>::HEAD;
#endif  // __cplusplus < 201703L
#if __cplusplus < 201703L
// static constexpr member variable definitions are only needed in C++14 and below, deprecated in C++17
template<typename ContainerAllocator>
constexpr uint8_t Retarget_<ContainerAllocator>::WAIST_HEAD;
#endif  // __cplusplus < 201703L
#if __cplusplus < 201703L
// static constexpr member variable definitions are only needed in C++14 and below, deprecated in C++17
template<typename ContainerAllocator>
constexpr uint8_t Retarget_<ContainerAllocator>::VR;
#endif  // __cplusplus < 201703L
#if __cplusplus < 201703L
// static constexpr member variable definitions are only needed in C++14 and below, deprecated in C++17
template<typename ContainerAllocator>
constexpr uint8_t Retarget_<ContainerAllocator>::MOCAP;
#endif  // __cplusplus < 201703L

}  // namespace msg

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__RETARGET__STRUCT_HPP_
