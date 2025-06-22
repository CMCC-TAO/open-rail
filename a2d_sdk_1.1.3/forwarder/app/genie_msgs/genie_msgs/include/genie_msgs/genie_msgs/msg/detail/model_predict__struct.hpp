// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from genie_msgs:msg/ModelPredict.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__MODEL_PREDICT__STRUCT_HPP_
#define GENIE_MSGS__MSG__DETAIL__MODEL_PREDICT__STRUCT_HPP_

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
// Member 'target_poses'
#include "geometry_msgs/msg/detail/pose__struct.hpp"
// Member 'target_joint_states'
#include "sensor_msgs/msg/detail/joint_state__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__genie_msgs__msg__ModelPredict __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__msg__ModelPredict __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct ModelPredict_
{
  using Type = ModelPredict_<ContainerAllocator>;

  explicit ModelPredict_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->model_output_type = 0;
      this->model_sleep_time = 0.0;
      this->trajectory_reference_time = 0.0;
    }
  }

  explicit ModelPredict_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->model_output_type = 0;
      this->model_sleep_time = 0.0;
      this->trajectory_reference_time = 0.0;
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _body_joint_names_type =
    std::vector<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>>>;
  _body_joint_names_type body_joint_names;
  using _body_joint_positions_type =
    std::vector<double, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<double>>;
  _body_joint_positions_type body_joint_positions;
  using _model_output_type_type =
    uint8_t;
  _model_output_type_type model_output_type;
  using _target_poses_type =
    std::vector<geometry_msgs::msg::Pose_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<geometry_msgs::msg::Pose_<ContainerAllocator>>>;
  _target_poses_type target_poses;
  using _target_joint_states_type =
    std::vector<sensor_msgs::msg::JointState_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<sensor_msgs::msg::JointState_<ContainerAllocator>>>;
  _target_joint_states_type target_joint_states;
  using _model_sleep_time_type =
    double;
  _model_sleep_time_type model_sleep_time;
  using _trajectory_reference_time_type =
    double;
  _trajectory_reference_time_type trajectory_reference_time;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
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
  Type & set__model_output_type(
    const uint8_t & _arg)
  {
    this->model_output_type = _arg;
    return *this;
  }
  Type & set__target_poses(
    const std::vector<geometry_msgs::msg::Pose_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<geometry_msgs::msg::Pose_<ContainerAllocator>>> & _arg)
  {
    this->target_poses = _arg;
    return *this;
  }
  Type & set__target_joint_states(
    const std::vector<sensor_msgs::msg::JointState_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<sensor_msgs::msg::JointState_<ContainerAllocator>>> & _arg)
  {
    this->target_joint_states = _arg;
    return *this;
  }
  Type & set__model_sleep_time(
    const double & _arg)
  {
    this->model_sleep_time = _arg;
    return *this;
  }
  Type & set__trajectory_reference_time(
    const double & _arg)
  {
    this->trajectory_reference_time = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::msg::ModelPredict_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::msg::ModelPredict_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::msg::ModelPredict_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::msg::ModelPredict_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::ModelPredict_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::ModelPredict_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::ModelPredict_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::ModelPredict_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::msg::ModelPredict_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::msg::ModelPredict_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__msg__ModelPredict
    std::shared_ptr<genie_msgs::msg::ModelPredict_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__msg__ModelPredict
    std::shared_ptr<genie_msgs::msg::ModelPredict_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const ModelPredict_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->body_joint_names != other.body_joint_names) {
      return false;
    }
    if (this->body_joint_positions != other.body_joint_positions) {
      return false;
    }
    if (this->model_output_type != other.model_output_type) {
      return false;
    }
    if (this->target_poses != other.target_poses) {
      return false;
    }
    if (this->target_joint_states != other.target_joint_states) {
      return false;
    }
    if (this->model_sleep_time != other.model_sleep_time) {
      return false;
    }
    if (this->trajectory_reference_time != other.trajectory_reference_time) {
      return false;
    }
    return true;
  }
  bool operator!=(const ModelPredict_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct ModelPredict_

// alias to use template instance with default allocator
using ModelPredict =
  genie_msgs::msg::ModelPredict_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__MODEL_PREDICT__STRUCT_HPP_
