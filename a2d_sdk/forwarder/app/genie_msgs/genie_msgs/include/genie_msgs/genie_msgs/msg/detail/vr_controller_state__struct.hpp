// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from genie_msgs:msg/VRControllerState.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__VR_CONTROLLER_STATE__STRUCT_HPP_
#define GENIE_MSGS__MSG__DETAIL__VR_CONTROLLER_STATE__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


// Include directives for member types
// Member 'position'
#include "geometry_msgs/msg/detail/vector3__struct.hpp"
// Member 'orientation'
#include "geometry_msgs/msg/detail/quaternion__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__genie_msgs__msg__VRControllerState __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__msg__VRControllerState __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct VRControllerState_
{
  using Type = VRControllerState_<ContainerAllocator>;

  explicit VRControllerState_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : position(_init),
    orientation(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->name = "";
      this->id = 0ul;
      this->key_one = false;
      this->key_two = false;
      this->hand_trig = 0.0;
      this->index_trig = 0.0;
      this->axis_x = 0.0;
      this->axis_y = 0.0;
      this->axis_click = false;
    }
  }

  explicit VRControllerState_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : name(_alloc),
    position(_alloc, _init),
    orientation(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->name = "";
      this->id = 0ul;
      this->key_one = false;
      this->key_two = false;
      this->hand_trig = 0.0;
      this->index_trig = 0.0;
      this->axis_x = 0.0;
      this->axis_y = 0.0;
      this->axis_click = false;
    }
  }

  // field types and members
  using _name_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _name_type name;
  using _id_type =
    uint32_t;
  _id_type id;
  using _key_one_type =
    bool;
  _key_one_type key_one;
  using _key_two_type =
    bool;
  _key_two_type key_two;
  using _hand_trig_type =
    double;
  _hand_trig_type hand_trig;
  using _index_trig_type =
    double;
  _index_trig_type index_trig;
  using _axis_x_type =
    double;
  _axis_x_type axis_x;
  using _axis_y_type =
    double;
  _axis_y_type axis_y;
  using _axis_click_type =
    bool;
  _axis_click_type axis_click;
  using _position_type =
    geometry_msgs::msg::Vector3_<ContainerAllocator>;
  _position_type position;
  using _orientation_type =
    geometry_msgs::msg::Quaternion_<ContainerAllocator>;
  _orientation_type orientation;

  // setters for named parameter idiom
  Type & set__name(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->name = _arg;
    return *this;
  }
  Type & set__id(
    const uint32_t & _arg)
  {
    this->id = _arg;
    return *this;
  }
  Type & set__key_one(
    const bool & _arg)
  {
    this->key_one = _arg;
    return *this;
  }
  Type & set__key_two(
    const bool & _arg)
  {
    this->key_two = _arg;
    return *this;
  }
  Type & set__hand_trig(
    const double & _arg)
  {
    this->hand_trig = _arg;
    return *this;
  }
  Type & set__index_trig(
    const double & _arg)
  {
    this->index_trig = _arg;
    return *this;
  }
  Type & set__axis_x(
    const double & _arg)
  {
    this->axis_x = _arg;
    return *this;
  }
  Type & set__axis_y(
    const double & _arg)
  {
    this->axis_y = _arg;
    return *this;
  }
  Type & set__axis_click(
    const bool & _arg)
  {
    this->axis_click = _arg;
    return *this;
  }
  Type & set__position(
    const geometry_msgs::msg::Vector3_<ContainerAllocator> & _arg)
  {
    this->position = _arg;
    return *this;
  }
  Type & set__orientation(
    const geometry_msgs::msg::Quaternion_<ContainerAllocator> & _arg)
  {
    this->orientation = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::msg::VRControllerState_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::msg::VRControllerState_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::msg::VRControllerState_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::msg::VRControllerState_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::VRControllerState_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::VRControllerState_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::VRControllerState_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::VRControllerState_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::msg::VRControllerState_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::msg::VRControllerState_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__msg__VRControllerState
    std::shared_ptr<genie_msgs::msg::VRControllerState_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__msg__VRControllerState
    std::shared_ptr<genie_msgs::msg::VRControllerState_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const VRControllerState_ & other) const
  {
    if (this->name != other.name) {
      return false;
    }
    if (this->id != other.id) {
      return false;
    }
    if (this->key_one != other.key_one) {
      return false;
    }
    if (this->key_two != other.key_two) {
      return false;
    }
    if (this->hand_trig != other.hand_trig) {
      return false;
    }
    if (this->index_trig != other.index_trig) {
      return false;
    }
    if (this->axis_x != other.axis_x) {
      return false;
    }
    if (this->axis_y != other.axis_y) {
      return false;
    }
    if (this->axis_click != other.axis_click) {
      return false;
    }
    if (this->position != other.position) {
      return false;
    }
    if (this->orientation != other.orientation) {
      return false;
    }
    return true;
  }
  bool operator!=(const VRControllerState_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct VRControllerState_

// alias to use template instance with default allocator
using VRControllerState =
  genie_msgs::msg::VRControllerState_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__VR_CONTROLLER_STATE__STRUCT_HPP_
