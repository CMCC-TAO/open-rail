// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from genie_msgs:msg/PeriCmd.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__PERI_CMD__STRUCT_HPP_
#define GENIE_MSGS__MSG__DETAIL__PERI_CMD__STRUCT_HPP_

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
# define DEPRECATED__genie_msgs__msg__PeriCmd __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__msg__PeriCmd __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct PeriCmd_
{
  using Type = PeriCmd_<ContainerAllocator>;

  explicit PeriCmd_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->compute_center_ready_shut_down = 0;
      this->soft_emergency_stop = 0;
      this->hub1_reset_request = 0;
      this->hub2_reset_request = 0;
      this->left_arm_reset_request = 0;
      this->right_arm_reset_request = 0;
      this->left_end_reset_request = 0;
      this->right_end_reset_request = 0;
      this->waist_pitch_motor_reset_request = 0;
      this->lift_motor_reset_request = 0;
      this->head_yaw_motor_reset_request = 0;
      this->head_pitch_motor_reset_request = 0;
      this->agv_reset_request = 0;
      this->work_mode = 0;
      this->feature_status = 0;
      this->left_arm_power_ctrl_req = 0;
      this->right_arm_power_ctrl_req = 0;
      this->left_end_power_ctrl_req = 0;
      this->right_end_power_ctrl_req = 0;
      this->waist_pitch_motor_power_ctrl_req = 0;
      this->lift_motor_power_ctrl_req = 0;
      this->head_yaw_motor_power_ctrl_req = 0;
      this->head_pitch_motor_power_ctrl_req = 0;
      this->agv_power_ctrl_req = 0;
    }
  }

  explicit PeriCmd_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->compute_center_ready_shut_down = 0;
      this->soft_emergency_stop = 0;
      this->hub1_reset_request = 0;
      this->hub2_reset_request = 0;
      this->left_arm_reset_request = 0;
      this->right_arm_reset_request = 0;
      this->left_end_reset_request = 0;
      this->right_end_reset_request = 0;
      this->waist_pitch_motor_reset_request = 0;
      this->lift_motor_reset_request = 0;
      this->head_yaw_motor_reset_request = 0;
      this->head_pitch_motor_reset_request = 0;
      this->agv_reset_request = 0;
      this->work_mode = 0;
      this->feature_status = 0;
      this->left_arm_power_ctrl_req = 0;
      this->right_arm_power_ctrl_req = 0;
      this->left_end_power_ctrl_req = 0;
      this->right_end_power_ctrl_req = 0;
      this->waist_pitch_motor_power_ctrl_req = 0;
      this->lift_motor_power_ctrl_req = 0;
      this->head_yaw_motor_power_ctrl_req = 0;
      this->head_pitch_motor_power_ctrl_req = 0;
      this->agv_power_ctrl_req = 0;
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _compute_center_ready_shut_down_type =
    uint8_t;
  _compute_center_ready_shut_down_type compute_center_ready_shut_down;
  using _soft_emergency_stop_type =
    uint8_t;
  _soft_emergency_stop_type soft_emergency_stop;
  using _hub1_reset_request_type =
    uint8_t;
  _hub1_reset_request_type hub1_reset_request;
  using _hub2_reset_request_type =
    uint8_t;
  _hub2_reset_request_type hub2_reset_request;
  using _left_arm_reset_request_type =
    uint8_t;
  _left_arm_reset_request_type left_arm_reset_request;
  using _right_arm_reset_request_type =
    uint8_t;
  _right_arm_reset_request_type right_arm_reset_request;
  using _left_end_reset_request_type =
    uint8_t;
  _left_end_reset_request_type left_end_reset_request;
  using _right_end_reset_request_type =
    uint8_t;
  _right_end_reset_request_type right_end_reset_request;
  using _waist_pitch_motor_reset_request_type =
    uint8_t;
  _waist_pitch_motor_reset_request_type waist_pitch_motor_reset_request;
  using _lift_motor_reset_request_type =
    uint8_t;
  _lift_motor_reset_request_type lift_motor_reset_request;
  using _head_yaw_motor_reset_request_type =
    uint8_t;
  _head_yaw_motor_reset_request_type head_yaw_motor_reset_request;
  using _head_pitch_motor_reset_request_type =
    uint8_t;
  _head_pitch_motor_reset_request_type head_pitch_motor_reset_request;
  using _agv_reset_request_type =
    uint8_t;
  _agv_reset_request_type agv_reset_request;
  using _work_mode_type =
    uint8_t;
  _work_mode_type work_mode;
  using _feature_status_type =
    uint8_t;
  _feature_status_type feature_status;
  using _left_arm_power_ctrl_req_type =
    uint8_t;
  _left_arm_power_ctrl_req_type left_arm_power_ctrl_req;
  using _right_arm_power_ctrl_req_type =
    uint8_t;
  _right_arm_power_ctrl_req_type right_arm_power_ctrl_req;
  using _left_end_power_ctrl_req_type =
    uint8_t;
  _left_end_power_ctrl_req_type left_end_power_ctrl_req;
  using _right_end_power_ctrl_req_type =
    uint8_t;
  _right_end_power_ctrl_req_type right_end_power_ctrl_req;
  using _waist_pitch_motor_power_ctrl_req_type =
    uint8_t;
  _waist_pitch_motor_power_ctrl_req_type waist_pitch_motor_power_ctrl_req;
  using _lift_motor_power_ctrl_req_type =
    uint8_t;
  _lift_motor_power_ctrl_req_type lift_motor_power_ctrl_req;
  using _head_yaw_motor_power_ctrl_req_type =
    uint8_t;
  _head_yaw_motor_power_ctrl_req_type head_yaw_motor_power_ctrl_req;
  using _head_pitch_motor_power_ctrl_req_type =
    uint8_t;
  _head_pitch_motor_power_ctrl_req_type head_pitch_motor_power_ctrl_req;
  using _agv_power_ctrl_req_type =
    uint8_t;
  _agv_power_ctrl_req_type agv_power_ctrl_req;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__compute_center_ready_shut_down(
    const uint8_t & _arg)
  {
    this->compute_center_ready_shut_down = _arg;
    return *this;
  }
  Type & set__soft_emergency_stop(
    const uint8_t & _arg)
  {
    this->soft_emergency_stop = _arg;
    return *this;
  }
  Type & set__hub1_reset_request(
    const uint8_t & _arg)
  {
    this->hub1_reset_request = _arg;
    return *this;
  }
  Type & set__hub2_reset_request(
    const uint8_t & _arg)
  {
    this->hub2_reset_request = _arg;
    return *this;
  }
  Type & set__left_arm_reset_request(
    const uint8_t & _arg)
  {
    this->left_arm_reset_request = _arg;
    return *this;
  }
  Type & set__right_arm_reset_request(
    const uint8_t & _arg)
  {
    this->right_arm_reset_request = _arg;
    return *this;
  }
  Type & set__left_end_reset_request(
    const uint8_t & _arg)
  {
    this->left_end_reset_request = _arg;
    return *this;
  }
  Type & set__right_end_reset_request(
    const uint8_t & _arg)
  {
    this->right_end_reset_request = _arg;
    return *this;
  }
  Type & set__waist_pitch_motor_reset_request(
    const uint8_t & _arg)
  {
    this->waist_pitch_motor_reset_request = _arg;
    return *this;
  }
  Type & set__lift_motor_reset_request(
    const uint8_t & _arg)
  {
    this->lift_motor_reset_request = _arg;
    return *this;
  }
  Type & set__head_yaw_motor_reset_request(
    const uint8_t & _arg)
  {
    this->head_yaw_motor_reset_request = _arg;
    return *this;
  }
  Type & set__head_pitch_motor_reset_request(
    const uint8_t & _arg)
  {
    this->head_pitch_motor_reset_request = _arg;
    return *this;
  }
  Type & set__agv_reset_request(
    const uint8_t & _arg)
  {
    this->agv_reset_request = _arg;
    return *this;
  }
  Type & set__work_mode(
    const uint8_t & _arg)
  {
    this->work_mode = _arg;
    return *this;
  }
  Type & set__feature_status(
    const uint8_t & _arg)
  {
    this->feature_status = _arg;
    return *this;
  }
  Type & set__left_arm_power_ctrl_req(
    const uint8_t & _arg)
  {
    this->left_arm_power_ctrl_req = _arg;
    return *this;
  }
  Type & set__right_arm_power_ctrl_req(
    const uint8_t & _arg)
  {
    this->right_arm_power_ctrl_req = _arg;
    return *this;
  }
  Type & set__left_end_power_ctrl_req(
    const uint8_t & _arg)
  {
    this->left_end_power_ctrl_req = _arg;
    return *this;
  }
  Type & set__right_end_power_ctrl_req(
    const uint8_t & _arg)
  {
    this->right_end_power_ctrl_req = _arg;
    return *this;
  }
  Type & set__waist_pitch_motor_power_ctrl_req(
    const uint8_t & _arg)
  {
    this->waist_pitch_motor_power_ctrl_req = _arg;
    return *this;
  }
  Type & set__lift_motor_power_ctrl_req(
    const uint8_t & _arg)
  {
    this->lift_motor_power_ctrl_req = _arg;
    return *this;
  }
  Type & set__head_yaw_motor_power_ctrl_req(
    const uint8_t & _arg)
  {
    this->head_yaw_motor_power_ctrl_req = _arg;
    return *this;
  }
  Type & set__head_pitch_motor_power_ctrl_req(
    const uint8_t & _arg)
  {
    this->head_pitch_motor_power_ctrl_req = _arg;
    return *this;
  }
  Type & set__agv_power_ctrl_req(
    const uint8_t & _arg)
  {
    this->agv_power_ctrl_req = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::msg::PeriCmd_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::msg::PeriCmd_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::msg::PeriCmd_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::msg::PeriCmd_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::PeriCmd_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::PeriCmd_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::PeriCmd_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::PeriCmd_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::msg::PeriCmd_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::msg::PeriCmd_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__msg__PeriCmd
    std::shared_ptr<genie_msgs::msg::PeriCmd_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__msg__PeriCmd
    std::shared_ptr<genie_msgs::msg::PeriCmd_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const PeriCmd_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->compute_center_ready_shut_down != other.compute_center_ready_shut_down) {
      return false;
    }
    if (this->soft_emergency_stop != other.soft_emergency_stop) {
      return false;
    }
    if (this->hub1_reset_request != other.hub1_reset_request) {
      return false;
    }
    if (this->hub2_reset_request != other.hub2_reset_request) {
      return false;
    }
    if (this->left_arm_reset_request != other.left_arm_reset_request) {
      return false;
    }
    if (this->right_arm_reset_request != other.right_arm_reset_request) {
      return false;
    }
    if (this->left_end_reset_request != other.left_end_reset_request) {
      return false;
    }
    if (this->right_end_reset_request != other.right_end_reset_request) {
      return false;
    }
    if (this->waist_pitch_motor_reset_request != other.waist_pitch_motor_reset_request) {
      return false;
    }
    if (this->lift_motor_reset_request != other.lift_motor_reset_request) {
      return false;
    }
    if (this->head_yaw_motor_reset_request != other.head_yaw_motor_reset_request) {
      return false;
    }
    if (this->head_pitch_motor_reset_request != other.head_pitch_motor_reset_request) {
      return false;
    }
    if (this->agv_reset_request != other.agv_reset_request) {
      return false;
    }
    if (this->work_mode != other.work_mode) {
      return false;
    }
    if (this->feature_status != other.feature_status) {
      return false;
    }
    if (this->left_arm_power_ctrl_req != other.left_arm_power_ctrl_req) {
      return false;
    }
    if (this->right_arm_power_ctrl_req != other.right_arm_power_ctrl_req) {
      return false;
    }
    if (this->left_end_power_ctrl_req != other.left_end_power_ctrl_req) {
      return false;
    }
    if (this->right_end_power_ctrl_req != other.right_end_power_ctrl_req) {
      return false;
    }
    if (this->waist_pitch_motor_power_ctrl_req != other.waist_pitch_motor_power_ctrl_req) {
      return false;
    }
    if (this->lift_motor_power_ctrl_req != other.lift_motor_power_ctrl_req) {
      return false;
    }
    if (this->head_yaw_motor_power_ctrl_req != other.head_yaw_motor_power_ctrl_req) {
      return false;
    }
    if (this->head_pitch_motor_power_ctrl_req != other.head_pitch_motor_power_ctrl_req) {
      return false;
    }
    if (this->agv_power_ctrl_req != other.agv_power_ctrl_req) {
      return false;
    }
    return true;
  }
  bool operator!=(const PeriCmd_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct PeriCmd_

// alias to use template instance with default allocator
using PeriCmd =
  genie_msgs::msg::PeriCmd_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__PERI_CMD__STRUCT_HPP_
