// NOLINT: This file starts with a BOM since it contain non-ASCII characters
// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from genie_msgs:msg/ArmState.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__ARM_STATE__STRUCT_H_
#define GENIE_MSGS__MSG__DETAIL__ARM_STATE__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.h"
// Member 'motor_states'
#include "genie_msgs/msg/detail/motor_state__struct.h"
// Member 'force_data'
#include "rosidl_runtime_c/primitives_sequence.h"

/// Struct defined in msg/ArmState in the package genie_msgs.
typedef struct genie_msgs__msg__ArmState
{
  std_msgs__msg__Header header;
  /// 每个关节的状态
  genie_msgs__msg__MotorState__Sequence motor_states;
  /// 六维力数据
  rosidl_runtime_c__double__Sequence force_data;
  /// 六维力坐标系
  int32_t force_coordinate;
  /// 六维力传感器状态：0 = 成功，1 = 失败，-1 = 通信失败，-2 = 数据接受失败，-3 = 返回值解析失败
  int32_t force_state;
  ///   kNormal                         = 0x0000    # 正常, 但是控制链路未建立
  ///   kNormalInControl                = 0x0001    # 正常，控制链路已建立
  ///   kJointCommErr                   = 0x1001 #关节通信异常。
  ///   kTargetAngleOutOfBounds         = 0x1002 #目标角度超过限位。
  ///   kSingularPointDetected          = 0x1003 #该处不可达，为奇异点。
  ///   kRTKernelCommError              = 0x1004 #实时内核通信错误。
  ///   kJointCommBusError              = 0x1005 #关节通信总线错误。
  ///   kPlanningLayerKernelError       = 0x1006 #规划层内核错误。
  ///   kJointOverSpeed                 = 0x1007 #关节超速。
  ///   kEndInterfaceBoardConnFailure   = 0x1008 #末端接口板无法连接。
  ///   kSpeedLimitExceeded             = 0x1009 #超速度限制。
  ///   kAccelLimitExceeded             = 0x100A #超加速度限制。
  ///   kJointBrakeNotReleased          = 0x100B #关节抱闸未打开。
  ///   kTeachModeOverSpeed             = 0x100C #拖动示教时超速。
  ///   kRobotArmCollision              = 0x100D #机械臂发生碰撞。
  ///   kWorkCoordSysNotFound           = 0x100E #无该工作坐标系。
  ///   kToolCoordSysNotFound           = 0x100F #无该工具坐标系。
  ///   kJointEnableLostError           = 0x1010 #关节发生掉使能错误。
  ///   kArcPlanningError               = 0x1011 #圆弧规划错误。
  ///   kSelfCollisionError             = 0x1012 #自碰撞错误。
  ///   kElecFenceCollisionError        = 0x1013 #碰撞到电子围栏错误。
  ///   kJointSoftLimitExceeded         = 0x1014 #超关节软限位错误。
  ///   kSixDimForceModuleAbnormal      = 0x2003 #六维力模块异常。
  ///                                   # 0x2004 #一维力模块异常。
  ///   kOutputCurrentAbnormal          = 0x2005 #输出电流异常。
  ///   kControllerOverTemp             = 0x5003 #控制器过温。
  ///   kControllerOverCurrent          = 0x5005 #控制器过流。
  ///   kControllerUnderCurrent         = 0x5006 #控制器欠流。
  ///   kControllerOverVoltage          = 0x5007 #控制器过压。
  ///   kControllerUnderVoltage         = 0x5008 #控制器欠压。
  ///   kOtherErr                       = 0x9000
  /// 机械臂状态, 参考以上枚举
  uint32_t arm_state;
  /// 系统错误码
  int32_t system_error;
} genie_msgs__msg__ArmState;

// Struct for a sequence of genie_msgs__msg__ArmState.
typedef struct genie_msgs__msg__ArmState__Sequence
{
  genie_msgs__msg__ArmState * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} genie_msgs__msg__ArmState__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__MSG__DETAIL__ARM_STATE__STRUCT_H_
