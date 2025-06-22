// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from genie_msgs:msg/Position.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__POSITION__STRUCT_HPP_
#define GENIE_MSGS__MSG__DETAIL__POSITION__STRUCT_HPP_

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
// Member 'motor_states'
#include "genie_msgs/msg/detail/motor_state__struct.hpp"
// Member 'agv_task_state'
#include "genie_msgs/msg/detail/agv_task_state__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__genie_msgs__msg__Position __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__msg__Position __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct Position_
{
  using Type = Position_<ContainerAllocator>;

  explicit Position_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init),
    agv_task_state(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->agv_status = 0l;
      this->position_conf = 0.0f;
      this->agv_pos_x = 0.0f;
      this->agv_pos_y = 0.0f;
      this->agv_pos_z = 0.0f;
      this->agv_angle = 0.0f;
      this->odom_x = 0.0f;
      this->odom_y = 0.0f;
      this->odom_z = 0.0f;
      this->odom_angle = 0.0f;
      this->linear_speed = 0.0f;
      this->angular_speed = 0.0f;
      this->acc_x = 0.0f;
      this->acc_y = 0.0f;
      this->acc_z = 0.0f;
      this->gyro_x = 0.0f;
      this->gyro_y = 0.0f;
      this->gyro_z = 0.0f;
      this->roll = 0.0f;
      this->pitch = 0.0f;
      this->yaw = 0.0f;
    }
  }

  explicit Position_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init),
    agv_task_state(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->agv_status = 0l;
      this->position_conf = 0.0f;
      this->agv_pos_x = 0.0f;
      this->agv_pos_y = 0.0f;
      this->agv_pos_z = 0.0f;
      this->agv_angle = 0.0f;
      this->odom_x = 0.0f;
      this->odom_y = 0.0f;
      this->odom_z = 0.0f;
      this->odom_angle = 0.0f;
      this->linear_speed = 0.0f;
      this->angular_speed = 0.0f;
      this->acc_x = 0.0f;
      this->acc_y = 0.0f;
      this->acc_z = 0.0f;
      this->gyro_x = 0.0f;
      this->gyro_y = 0.0f;
      this->gyro_z = 0.0f;
      this->roll = 0.0f;
      this->pitch = 0.0f;
      this->yaw = 0.0f;
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _agv_status_type =
    int32_t;
  _agv_status_type agv_status;
  using _position_conf_type =
    float;
  _position_conf_type position_conf;
  using _agv_pos_x_type =
    float;
  _agv_pos_x_type agv_pos_x;
  using _agv_pos_y_type =
    float;
  _agv_pos_y_type agv_pos_y;
  using _agv_pos_z_type =
    float;
  _agv_pos_z_type agv_pos_z;
  using _agv_angle_type =
    float;
  _agv_angle_type agv_angle;
  using _odom_x_type =
    float;
  _odom_x_type odom_x;
  using _odom_y_type =
    float;
  _odom_y_type odom_y;
  using _odom_z_type =
    float;
  _odom_z_type odom_z;
  using _odom_angle_type =
    float;
  _odom_angle_type odom_angle;
  using _linear_speed_type =
    float;
  _linear_speed_type linear_speed;
  using _angular_speed_type =
    float;
  _angular_speed_type angular_speed;
  using _acc_x_type =
    float;
  _acc_x_type acc_x;
  using _acc_y_type =
    float;
  _acc_y_type acc_y;
  using _acc_z_type =
    float;
  _acc_z_type acc_z;
  using _gyro_x_type =
    float;
  _gyro_x_type gyro_x;
  using _gyro_y_type =
    float;
  _gyro_y_type gyro_y;
  using _gyro_z_type =
    float;
  _gyro_z_type gyro_z;
  using _roll_type =
    float;
  _roll_type roll;
  using _pitch_type =
    float;
  _pitch_type pitch;
  using _yaw_type =
    float;
  _yaw_type yaw;
  using _motor_states_type =
    std::vector<genie_msgs::msg::MotorState_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<genie_msgs::msg::MotorState_<ContainerAllocator>>>;
  _motor_states_type motor_states;
  using _agv_task_state_type =
    genie_msgs::msg::AGVTaskState_<ContainerAllocator>;
  _agv_task_state_type agv_task_state;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__agv_status(
    const int32_t & _arg)
  {
    this->agv_status = _arg;
    return *this;
  }
  Type & set__position_conf(
    const float & _arg)
  {
    this->position_conf = _arg;
    return *this;
  }
  Type & set__agv_pos_x(
    const float & _arg)
  {
    this->agv_pos_x = _arg;
    return *this;
  }
  Type & set__agv_pos_y(
    const float & _arg)
  {
    this->agv_pos_y = _arg;
    return *this;
  }
  Type & set__agv_pos_z(
    const float & _arg)
  {
    this->agv_pos_z = _arg;
    return *this;
  }
  Type & set__agv_angle(
    const float & _arg)
  {
    this->agv_angle = _arg;
    return *this;
  }
  Type & set__odom_x(
    const float & _arg)
  {
    this->odom_x = _arg;
    return *this;
  }
  Type & set__odom_y(
    const float & _arg)
  {
    this->odom_y = _arg;
    return *this;
  }
  Type & set__odom_z(
    const float & _arg)
  {
    this->odom_z = _arg;
    return *this;
  }
  Type & set__odom_angle(
    const float & _arg)
  {
    this->odom_angle = _arg;
    return *this;
  }
  Type & set__linear_speed(
    const float & _arg)
  {
    this->linear_speed = _arg;
    return *this;
  }
  Type & set__angular_speed(
    const float & _arg)
  {
    this->angular_speed = _arg;
    return *this;
  }
  Type & set__acc_x(
    const float & _arg)
  {
    this->acc_x = _arg;
    return *this;
  }
  Type & set__acc_y(
    const float & _arg)
  {
    this->acc_y = _arg;
    return *this;
  }
  Type & set__acc_z(
    const float & _arg)
  {
    this->acc_z = _arg;
    return *this;
  }
  Type & set__gyro_x(
    const float & _arg)
  {
    this->gyro_x = _arg;
    return *this;
  }
  Type & set__gyro_y(
    const float & _arg)
  {
    this->gyro_y = _arg;
    return *this;
  }
  Type & set__gyro_z(
    const float & _arg)
  {
    this->gyro_z = _arg;
    return *this;
  }
  Type & set__roll(
    const float & _arg)
  {
    this->roll = _arg;
    return *this;
  }
  Type & set__pitch(
    const float & _arg)
  {
    this->pitch = _arg;
    return *this;
  }
  Type & set__yaw(
    const float & _arg)
  {
    this->yaw = _arg;
    return *this;
  }
  Type & set__motor_states(
    const std::vector<genie_msgs::msg::MotorState_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<genie_msgs::msg::MotorState_<ContainerAllocator>>> & _arg)
  {
    this->motor_states = _arg;
    return *this;
  }
  Type & set__agv_task_state(
    const genie_msgs::msg::AGVTaskState_<ContainerAllocator> & _arg)
  {
    this->agv_task_state = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::msg::Position_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::msg::Position_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::msg::Position_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::msg::Position_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::Position_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::Position_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::Position_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::Position_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::msg::Position_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::msg::Position_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__msg__Position
    std::shared_ptr<genie_msgs::msg::Position_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__msg__Position
    std::shared_ptr<genie_msgs::msg::Position_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const Position_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->agv_status != other.agv_status) {
      return false;
    }
    if (this->position_conf != other.position_conf) {
      return false;
    }
    if (this->agv_pos_x != other.agv_pos_x) {
      return false;
    }
    if (this->agv_pos_y != other.agv_pos_y) {
      return false;
    }
    if (this->agv_pos_z != other.agv_pos_z) {
      return false;
    }
    if (this->agv_angle != other.agv_angle) {
      return false;
    }
    if (this->odom_x != other.odom_x) {
      return false;
    }
    if (this->odom_y != other.odom_y) {
      return false;
    }
    if (this->odom_z != other.odom_z) {
      return false;
    }
    if (this->odom_angle != other.odom_angle) {
      return false;
    }
    if (this->linear_speed != other.linear_speed) {
      return false;
    }
    if (this->angular_speed != other.angular_speed) {
      return false;
    }
    if (this->acc_x != other.acc_x) {
      return false;
    }
    if (this->acc_y != other.acc_y) {
      return false;
    }
    if (this->acc_z != other.acc_z) {
      return false;
    }
    if (this->gyro_x != other.gyro_x) {
      return false;
    }
    if (this->gyro_y != other.gyro_y) {
      return false;
    }
    if (this->gyro_z != other.gyro_z) {
      return false;
    }
    if (this->roll != other.roll) {
      return false;
    }
    if (this->pitch != other.pitch) {
      return false;
    }
    if (this->yaw != other.yaw) {
      return false;
    }
    if (this->motor_states != other.motor_states) {
      return false;
    }
    if (this->agv_task_state != other.agv_task_state) {
      return false;
    }
    return true;
  }
  bool operator!=(const Position_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct Position_

// alias to use template instance with default allocator
using Position =
  genie_msgs::msg::Position_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__POSITION__STRUCT_HPP_
