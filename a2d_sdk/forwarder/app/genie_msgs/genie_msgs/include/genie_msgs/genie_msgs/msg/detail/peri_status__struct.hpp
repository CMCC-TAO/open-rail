// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from genie_msgs:msg/PeriStatus.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__PERI_STATUS__STRUCT_HPP_
#define GENIE_MSGS__MSG__DETAIL__PERI_STATUS__STRUCT_HPP_

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
# define DEPRECATED__genie_msgs__msg__PeriStatus __attribute__((deprecated))
#else
# define DEPRECATED__genie_msgs__msg__PeriStatus __declspec(deprecated)
#endif

namespace genie_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct PeriStatus_
{
  using Type = PeriStatus_<ContainerAllocator>;

  explicit PeriStatus_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->shut_down_compute_center_request = 0;
      this->soft_emergency_stop_feedback = 0;
      this->pedal_emergency_stop = 0;
      this->button_emergency_stop = 0;
      this->hub1_reset_request_feedback = 0;
      this->hub2_reset_request_feedback = 0;
      this->left_arm_reset_request_feedback = 0;
      this->right_arm_reset_request_feedback = 0;
      this->left_end_reset_request_feedback = 0;
      this->right_end_reset_request_feedback = 0;
      this->waist_pitch_motor_reset_request_feedback = 0;
      this->lift_motor_reset_request_feedback = 0;
      this->head_yaw_motor_reset_request_feedback = 0;
      this->head_pitch_motor_reset_request_feedback = 0;
      this->agv_reset_request_feedback = 0;
      this->power_pcb_work_mode = 0;
      this->feature_status = 0;
      this->left_arm_power_ctrl_req_feedback = 0;
      this->right_arm_power_ctrl_req_feedback = 0;
      this->left_end_power_ctrl_req_feedback = 0;
      this->right_end_power_ctrl_req_feedback = 0;
      this->waist_pitch_motor_power_ctrl_req_feedback = 0;
      this->lift_motor_power_ctrl_req_feedback = 0;
      this->head_yaw_motor_power_ctrl_req_feedback = 0;
      this->head_pitch_motor_power_ctrl_req_feedback = 0;
      this->agv_power_ctrl_req_feedback = 0;
      this->power_ctrl_req_failreason = 0;
      this->left_end_current = 0.0f;
      this->right_end_current = 0.0f;
      this->waist_pitch_motor_current = 0.0f;
      this->lift_motor_current = 0.0f;
      this->head_yaw_motor_current = 0.0f;
      this->head_pitch_motor_current = 0.0f;
      this->agv_current = 0.0f;
      this->left_end_voltage = 0.0f;
      this->right_end_voltage = 0.0f;
      this->waist_pitch_motor_voltage = 0.0f;
      this->lift_motor_voltage = 0.0f;
      this->head_yaw_motor_voltage = 0.0f;
      this->head_pitch_motor_voltage = 0.0f;
      this->agv_voltage = 0.0f;
      this->emergency_stop_err_fedback = 0;
      this->power_board_software_version = "";
      this->power_board_hardware_version = "";
      this->power_board_serial_number = "";
    }
  }

  explicit PeriStatus_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init),
    power_board_software_version(_alloc),
    power_board_hardware_version(_alloc),
    power_board_serial_number(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->shut_down_compute_center_request = 0;
      this->soft_emergency_stop_feedback = 0;
      this->pedal_emergency_stop = 0;
      this->button_emergency_stop = 0;
      this->hub1_reset_request_feedback = 0;
      this->hub2_reset_request_feedback = 0;
      this->left_arm_reset_request_feedback = 0;
      this->right_arm_reset_request_feedback = 0;
      this->left_end_reset_request_feedback = 0;
      this->right_end_reset_request_feedback = 0;
      this->waist_pitch_motor_reset_request_feedback = 0;
      this->lift_motor_reset_request_feedback = 0;
      this->head_yaw_motor_reset_request_feedback = 0;
      this->head_pitch_motor_reset_request_feedback = 0;
      this->agv_reset_request_feedback = 0;
      this->power_pcb_work_mode = 0;
      this->feature_status = 0;
      this->left_arm_power_ctrl_req_feedback = 0;
      this->right_arm_power_ctrl_req_feedback = 0;
      this->left_end_power_ctrl_req_feedback = 0;
      this->right_end_power_ctrl_req_feedback = 0;
      this->waist_pitch_motor_power_ctrl_req_feedback = 0;
      this->lift_motor_power_ctrl_req_feedback = 0;
      this->head_yaw_motor_power_ctrl_req_feedback = 0;
      this->head_pitch_motor_power_ctrl_req_feedback = 0;
      this->agv_power_ctrl_req_feedback = 0;
      this->power_ctrl_req_failreason = 0;
      this->left_end_current = 0.0f;
      this->right_end_current = 0.0f;
      this->waist_pitch_motor_current = 0.0f;
      this->lift_motor_current = 0.0f;
      this->head_yaw_motor_current = 0.0f;
      this->head_pitch_motor_current = 0.0f;
      this->agv_current = 0.0f;
      this->left_end_voltage = 0.0f;
      this->right_end_voltage = 0.0f;
      this->waist_pitch_motor_voltage = 0.0f;
      this->lift_motor_voltage = 0.0f;
      this->head_yaw_motor_voltage = 0.0f;
      this->head_pitch_motor_voltage = 0.0f;
      this->agv_voltage = 0.0f;
      this->emergency_stop_err_fedback = 0;
      this->power_board_software_version = "";
      this->power_board_hardware_version = "";
      this->power_board_serial_number = "";
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _shut_down_compute_center_request_type =
    uint8_t;
  _shut_down_compute_center_request_type shut_down_compute_center_request;
  using _soft_emergency_stop_feedback_type =
    uint8_t;
  _soft_emergency_stop_feedback_type soft_emergency_stop_feedback;
  using _pedal_emergency_stop_type =
    uint8_t;
  _pedal_emergency_stop_type pedal_emergency_stop;
  using _button_emergency_stop_type =
    uint8_t;
  _button_emergency_stop_type button_emergency_stop;
  using _hub1_reset_request_feedback_type =
    uint8_t;
  _hub1_reset_request_feedback_type hub1_reset_request_feedback;
  using _hub2_reset_request_feedback_type =
    uint8_t;
  _hub2_reset_request_feedback_type hub2_reset_request_feedback;
  using _left_arm_reset_request_feedback_type =
    uint8_t;
  _left_arm_reset_request_feedback_type left_arm_reset_request_feedback;
  using _right_arm_reset_request_feedback_type =
    uint8_t;
  _right_arm_reset_request_feedback_type right_arm_reset_request_feedback;
  using _left_end_reset_request_feedback_type =
    uint8_t;
  _left_end_reset_request_feedback_type left_end_reset_request_feedback;
  using _right_end_reset_request_feedback_type =
    uint8_t;
  _right_end_reset_request_feedback_type right_end_reset_request_feedback;
  using _waist_pitch_motor_reset_request_feedback_type =
    uint8_t;
  _waist_pitch_motor_reset_request_feedback_type waist_pitch_motor_reset_request_feedback;
  using _lift_motor_reset_request_feedback_type =
    uint8_t;
  _lift_motor_reset_request_feedback_type lift_motor_reset_request_feedback;
  using _head_yaw_motor_reset_request_feedback_type =
    uint8_t;
  _head_yaw_motor_reset_request_feedback_type head_yaw_motor_reset_request_feedback;
  using _head_pitch_motor_reset_request_feedback_type =
    uint8_t;
  _head_pitch_motor_reset_request_feedback_type head_pitch_motor_reset_request_feedback;
  using _agv_reset_request_feedback_type =
    uint8_t;
  _agv_reset_request_feedback_type agv_reset_request_feedback;
  using _power_pcb_work_mode_type =
    uint8_t;
  _power_pcb_work_mode_type power_pcb_work_mode;
  using _feature_status_type =
    uint8_t;
  _feature_status_type feature_status;
  using _left_arm_power_ctrl_req_feedback_type =
    uint8_t;
  _left_arm_power_ctrl_req_feedback_type left_arm_power_ctrl_req_feedback;
  using _right_arm_power_ctrl_req_feedback_type =
    uint8_t;
  _right_arm_power_ctrl_req_feedback_type right_arm_power_ctrl_req_feedback;
  using _left_end_power_ctrl_req_feedback_type =
    uint8_t;
  _left_end_power_ctrl_req_feedback_type left_end_power_ctrl_req_feedback;
  using _right_end_power_ctrl_req_feedback_type =
    uint8_t;
  _right_end_power_ctrl_req_feedback_type right_end_power_ctrl_req_feedback;
  using _waist_pitch_motor_power_ctrl_req_feedback_type =
    uint8_t;
  _waist_pitch_motor_power_ctrl_req_feedback_type waist_pitch_motor_power_ctrl_req_feedback;
  using _lift_motor_power_ctrl_req_feedback_type =
    uint8_t;
  _lift_motor_power_ctrl_req_feedback_type lift_motor_power_ctrl_req_feedback;
  using _head_yaw_motor_power_ctrl_req_feedback_type =
    uint8_t;
  _head_yaw_motor_power_ctrl_req_feedback_type head_yaw_motor_power_ctrl_req_feedback;
  using _head_pitch_motor_power_ctrl_req_feedback_type =
    uint8_t;
  _head_pitch_motor_power_ctrl_req_feedback_type head_pitch_motor_power_ctrl_req_feedback;
  using _agv_power_ctrl_req_feedback_type =
    uint8_t;
  _agv_power_ctrl_req_feedback_type agv_power_ctrl_req_feedback;
  using _power_ctrl_req_failreason_type =
    uint8_t;
  _power_ctrl_req_failreason_type power_ctrl_req_failreason;
  using _left_end_current_type =
    float;
  _left_end_current_type left_end_current;
  using _right_end_current_type =
    float;
  _right_end_current_type right_end_current;
  using _waist_pitch_motor_current_type =
    float;
  _waist_pitch_motor_current_type waist_pitch_motor_current;
  using _lift_motor_current_type =
    float;
  _lift_motor_current_type lift_motor_current;
  using _head_yaw_motor_current_type =
    float;
  _head_yaw_motor_current_type head_yaw_motor_current;
  using _head_pitch_motor_current_type =
    float;
  _head_pitch_motor_current_type head_pitch_motor_current;
  using _agv_current_type =
    float;
  _agv_current_type agv_current;
  using _left_end_voltage_type =
    float;
  _left_end_voltage_type left_end_voltage;
  using _right_end_voltage_type =
    float;
  _right_end_voltage_type right_end_voltage;
  using _waist_pitch_motor_voltage_type =
    float;
  _waist_pitch_motor_voltage_type waist_pitch_motor_voltage;
  using _lift_motor_voltage_type =
    float;
  _lift_motor_voltage_type lift_motor_voltage;
  using _head_yaw_motor_voltage_type =
    float;
  _head_yaw_motor_voltage_type head_yaw_motor_voltage;
  using _head_pitch_motor_voltage_type =
    float;
  _head_pitch_motor_voltage_type head_pitch_motor_voltage;
  using _agv_voltage_type =
    float;
  _agv_voltage_type agv_voltage;
  using _emergency_stop_err_fedback_type =
    uint8_t;
  _emergency_stop_err_fedback_type emergency_stop_err_fedback;
  using _power_board_software_version_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _power_board_software_version_type power_board_software_version;
  using _power_board_hardware_version_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _power_board_hardware_version_type power_board_hardware_version;
  using _power_board_serial_number_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _power_board_serial_number_type power_board_serial_number;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__shut_down_compute_center_request(
    const uint8_t & _arg)
  {
    this->shut_down_compute_center_request = _arg;
    return *this;
  }
  Type & set__soft_emergency_stop_feedback(
    const uint8_t & _arg)
  {
    this->soft_emergency_stop_feedback = _arg;
    return *this;
  }
  Type & set__pedal_emergency_stop(
    const uint8_t & _arg)
  {
    this->pedal_emergency_stop = _arg;
    return *this;
  }
  Type & set__button_emergency_stop(
    const uint8_t & _arg)
  {
    this->button_emergency_stop = _arg;
    return *this;
  }
  Type & set__hub1_reset_request_feedback(
    const uint8_t & _arg)
  {
    this->hub1_reset_request_feedback = _arg;
    return *this;
  }
  Type & set__hub2_reset_request_feedback(
    const uint8_t & _arg)
  {
    this->hub2_reset_request_feedback = _arg;
    return *this;
  }
  Type & set__left_arm_reset_request_feedback(
    const uint8_t & _arg)
  {
    this->left_arm_reset_request_feedback = _arg;
    return *this;
  }
  Type & set__right_arm_reset_request_feedback(
    const uint8_t & _arg)
  {
    this->right_arm_reset_request_feedback = _arg;
    return *this;
  }
  Type & set__left_end_reset_request_feedback(
    const uint8_t & _arg)
  {
    this->left_end_reset_request_feedback = _arg;
    return *this;
  }
  Type & set__right_end_reset_request_feedback(
    const uint8_t & _arg)
  {
    this->right_end_reset_request_feedback = _arg;
    return *this;
  }
  Type & set__waist_pitch_motor_reset_request_feedback(
    const uint8_t & _arg)
  {
    this->waist_pitch_motor_reset_request_feedback = _arg;
    return *this;
  }
  Type & set__lift_motor_reset_request_feedback(
    const uint8_t & _arg)
  {
    this->lift_motor_reset_request_feedback = _arg;
    return *this;
  }
  Type & set__head_yaw_motor_reset_request_feedback(
    const uint8_t & _arg)
  {
    this->head_yaw_motor_reset_request_feedback = _arg;
    return *this;
  }
  Type & set__head_pitch_motor_reset_request_feedback(
    const uint8_t & _arg)
  {
    this->head_pitch_motor_reset_request_feedback = _arg;
    return *this;
  }
  Type & set__agv_reset_request_feedback(
    const uint8_t & _arg)
  {
    this->agv_reset_request_feedback = _arg;
    return *this;
  }
  Type & set__power_pcb_work_mode(
    const uint8_t & _arg)
  {
    this->power_pcb_work_mode = _arg;
    return *this;
  }
  Type & set__feature_status(
    const uint8_t & _arg)
  {
    this->feature_status = _arg;
    return *this;
  }
  Type & set__left_arm_power_ctrl_req_feedback(
    const uint8_t & _arg)
  {
    this->left_arm_power_ctrl_req_feedback = _arg;
    return *this;
  }
  Type & set__right_arm_power_ctrl_req_feedback(
    const uint8_t & _arg)
  {
    this->right_arm_power_ctrl_req_feedback = _arg;
    return *this;
  }
  Type & set__left_end_power_ctrl_req_feedback(
    const uint8_t & _arg)
  {
    this->left_end_power_ctrl_req_feedback = _arg;
    return *this;
  }
  Type & set__right_end_power_ctrl_req_feedback(
    const uint8_t & _arg)
  {
    this->right_end_power_ctrl_req_feedback = _arg;
    return *this;
  }
  Type & set__waist_pitch_motor_power_ctrl_req_feedback(
    const uint8_t & _arg)
  {
    this->waist_pitch_motor_power_ctrl_req_feedback = _arg;
    return *this;
  }
  Type & set__lift_motor_power_ctrl_req_feedback(
    const uint8_t & _arg)
  {
    this->lift_motor_power_ctrl_req_feedback = _arg;
    return *this;
  }
  Type & set__head_yaw_motor_power_ctrl_req_feedback(
    const uint8_t & _arg)
  {
    this->head_yaw_motor_power_ctrl_req_feedback = _arg;
    return *this;
  }
  Type & set__head_pitch_motor_power_ctrl_req_feedback(
    const uint8_t & _arg)
  {
    this->head_pitch_motor_power_ctrl_req_feedback = _arg;
    return *this;
  }
  Type & set__agv_power_ctrl_req_feedback(
    const uint8_t & _arg)
  {
    this->agv_power_ctrl_req_feedback = _arg;
    return *this;
  }
  Type & set__power_ctrl_req_failreason(
    const uint8_t & _arg)
  {
    this->power_ctrl_req_failreason = _arg;
    return *this;
  }
  Type & set__left_end_current(
    const float & _arg)
  {
    this->left_end_current = _arg;
    return *this;
  }
  Type & set__right_end_current(
    const float & _arg)
  {
    this->right_end_current = _arg;
    return *this;
  }
  Type & set__waist_pitch_motor_current(
    const float & _arg)
  {
    this->waist_pitch_motor_current = _arg;
    return *this;
  }
  Type & set__lift_motor_current(
    const float & _arg)
  {
    this->lift_motor_current = _arg;
    return *this;
  }
  Type & set__head_yaw_motor_current(
    const float & _arg)
  {
    this->head_yaw_motor_current = _arg;
    return *this;
  }
  Type & set__head_pitch_motor_current(
    const float & _arg)
  {
    this->head_pitch_motor_current = _arg;
    return *this;
  }
  Type & set__agv_current(
    const float & _arg)
  {
    this->agv_current = _arg;
    return *this;
  }
  Type & set__left_end_voltage(
    const float & _arg)
  {
    this->left_end_voltage = _arg;
    return *this;
  }
  Type & set__right_end_voltage(
    const float & _arg)
  {
    this->right_end_voltage = _arg;
    return *this;
  }
  Type & set__waist_pitch_motor_voltage(
    const float & _arg)
  {
    this->waist_pitch_motor_voltage = _arg;
    return *this;
  }
  Type & set__lift_motor_voltage(
    const float & _arg)
  {
    this->lift_motor_voltage = _arg;
    return *this;
  }
  Type & set__head_yaw_motor_voltage(
    const float & _arg)
  {
    this->head_yaw_motor_voltage = _arg;
    return *this;
  }
  Type & set__head_pitch_motor_voltage(
    const float & _arg)
  {
    this->head_pitch_motor_voltage = _arg;
    return *this;
  }
  Type & set__agv_voltage(
    const float & _arg)
  {
    this->agv_voltage = _arg;
    return *this;
  }
  Type & set__emergency_stop_err_fedback(
    const uint8_t & _arg)
  {
    this->emergency_stop_err_fedback = _arg;
    return *this;
  }
  Type & set__power_board_software_version(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->power_board_software_version = _arg;
    return *this;
  }
  Type & set__power_board_hardware_version(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->power_board_hardware_version = _arg;
    return *this;
  }
  Type & set__power_board_serial_number(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->power_board_serial_number = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    genie_msgs::msg::PeriStatus_<ContainerAllocator> *;
  using ConstRawPtr =
    const genie_msgs::msg::PeriStatus_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<genie_msgs::msg::PeriStatus_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<genie_msgs::msg::PeriStatus_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::PeriStatus_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::PeriStatus_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      genie_msgs::msg::PeriStatus_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<genie_msgs::msg::PeriStatus_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<genie_msgs::msg::PeriStatus_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<genie_msgs::msg::PeriStatus_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__genie_msgs__msg__PeriStatus
    std::shared_ptr<genie_msgs::msg::PeriStatus_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__genie_msgs__msg__PeriStatus
    std::shared_ptr<genie_msgs::msg::PeriStatus_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const PeriStatus_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->shut_down_compute_center_request != other.shut_down_compute_center_request) {
      return false;
    }
    if (this->soft_emergency_stop_feedback != other.soft_emergency_stop_feedback) {
      return false;
    }
    if (this->pedal_emergency_stop != other.pedal_emergency_stop) {
      return false;
    }
    if (this->button_emergency_stop != other.button_emergency_stop) {
      return false;
    }
    if (this->hub1_reset_request_feedback != other.hub1_reset_request_feedback) {
      return false;
    }
    if (this->hub2_reset_request_feedback != other.hub2_reset_request_feedback) {
      return false;
    }
    if (this->left_arm_reset_request_feedback != other.left_arm_reset_request_feedback) {
      return false;
    }
    if (this->right_arm_reset_request_feedback != other.right_arm_reset_request_feedback) {
      return false;
    }
    if (this->left_end_reset_request_feedback != other.left_end_reset_request_feedback) {
      return false;
    }
    if (this->right_end_reset_request_feedback != other.right_end_reset_request_feedback) {
      return false;
    }
    if (this->waist_pitch_motor_reset_request_feedback != other.waist_pitch_motor_reset_request_feedback) {
      return false;
    }
    if (this->lift_motor_reset_request_feedback != other.lift_motor_reset_request_feedback) {
      return false;
    }
    if (this->head_yaw_motor_reset_request_feedback != other.head_yaw_motor_reset_request_feedback) {
      return false;
    }
    if (this->head_pitch_motor_reset_request_feedback != other.head_pitch_motor_reset_request_feedback) {
      return false;
    }
    if (this->agv_reset_request_feedback != other.agv_reset_request_feedback) {
      return false;
    }
    if (this->power_pcb_work_mode != other.power_pcb_work_mode) {
      return false;
    }
    if (this->feature_status != other.feature_status) {
      return false;
    }
    if (this->left_arm_power_ctrl_req_feedback != other.left_arm_power_ctrl_req_feedback) {
      return false;
    }
    if (this->right_arm_power_ctrl_req_feedback != other.right_arm_power_ctrl_req_feedback) {
      return false;
    }
    if (this->left_end_power_ctrl_req_feedback != other.left_end_power_ctrl_req_feedback) {
      return false;
    }
    if (this->right_end_power_ctrl_req_feedback != other.right_end_power_ctrl_req_feedback) {
      return false;
    }
    if (this->waist_pitch_motor_power_ctrl_req_feedback != other.waist_pitch_motor_power_ctrl_req_feedback) {
      return false;
    }
    if (this->lift_motor_power_ctrl_req_feedback != other.lift_motor_power_ctrl_req_feedback) {
      return false;
    }
    if (this->head_yaw_motor_power_ctrl_req_feedback != other.head_yaw_motor_power_ctrl_req_feedback) {
      return false;
    }
    if (this->head_pitch_motor_power_ctrl_req_feedback != other.head_pitch_motor_power_ctrl_req_feedback) {
      return false;
    }
    if (this->agv_power_ctrl_req_feedback != other.agv_power_ctrl_req_feedback) {
      return false;
    }
    if (this->power_ctrl_req_failreason != other.power_ctrl_req_failreason) {
      return false;
    }
    if (this->left_end_current != other.left_end_current) {
      return false;
    }
    if (this->right_end_current != other.right_end_current) {
      return false;
    }
    if (this->waist_pitch_motor_current != other.waist_pitch_motor_current) {
      return false;
    }
    if (this->lift_motor_current != other.lift_motor_current) {
      return false;
    }
    if (this->head_yaw_motor_current != other.head_yaw_motor_current) {
      return false;
    }
    if (this->head_pitch_motor_current != other.head_pitch_motor_current) {
      return false;
    }
    if (this->agv_current != other.agv_current) {
      return false;
    }
    if (this->left_end_voltage != other.left_end_voltage) {
      return false;
    }
    if (this->right_end_voltage != other.right_end_voltage) {
      return false;
    }
    if (this->waist_pitch_motor_voltage != other.waist_pitch_motor_voltage) {
      return false;
    }
    if (this->lift_motor_voltage != other.lift_motor_voltage) {
      return false;
    }
    if (this->head_yaw_motor_voltage != other.head_yaw_motor_voltage) {
      return false;
    }
    if (this->head_pitch_motor_voltage != other.head_pitch_motor_voltage) {
      return false;
    }
    if (this->agv_voltage != other.agv_voltage) {
      return false;
    }
    if (this->emergency_stop_err_fedback != other.emergency_stop_err_fedback) {
      return false;
    }
    if (this->power_board_software_version != other.power_board_software_version) {
      return false;
    }
    if (this->power_board_hardware_version != other.power_board_hardware_version) {
      return false;
    }
    if (this->power_board_serial_number != other.power_board_serial_number) {
      return false;
    }
    return true;
  }
  bool operator!=(const PeriStatus_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct PeriStatus_

// alias to use template instance with default allocator
using PeriStatus =
  genie_msgs::msg::PeriStatus_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace genie_msgs

#endif  // GENIE_MSGS__MSG__DETAIL__PERI_STATUS__STRUCT_HPP_
