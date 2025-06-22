// generated from rosidl_generator_c/resource/idl__functions.h.em
// with input from genie_msgs:msg/CalibrateStatus.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__CALIBRATE_STATUS__FUNCTIONS_H_
#define GENIE_MSGS__MSG__DETAIL__CALIBRATE_STATUS__FUNCTIONS_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stdlib.h>

#include "rosidl_runtime_c/visibility_control.h"
#include "genie_msgs/msg/rosidl_generator_c__visibility_control.h"

#include "genie_msgs/msg/detail/calibrate_status__struct.h"

/// Initialize msg/CalibrateStatus message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * genie_msgs__msg__CalibrateStatus
 * )) before or use
 * genie_msgs__msg__CalibrateStatus__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_genie_msgs
bool
genie_msgs__msg__CalibrateStatus__init(genie_msgs__msg__CalibrateStatus * msg);

/// Finalize msg/CalibrateStatus message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_genie_msgs
void
genie_msgs__msg__CalibrateStatus__fini(genie_msgs__msg__CalibrateStatus * msg);

/// Create msg/CalibrateStatus message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * genie_msgs__msg__CalibrateStatus__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_genie_msgs
genie_msgs__msg__CalibrateStatus *
genie_msgs__msg__CalibrateStatus__create();

/// Destroy msg/CalibrateStatus message.
/**
 * It calls
 * genie_msgs__msg__CalibrateStatus__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_genie_msgs
void
genie_msgs__msg__CalibrateStatus__destroy(genie_msgs__msg__CalibrateStatus * msg);

/// Check for msg/CalibrateStatus message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_genie_msgs
bool
genie_msgs__msg__CalibrateStatus__are_equal(const genie_msgs__msg__CalibrateStatus * lhs, const genie_msgs__msg__CalibrateStatus * rhs);

/// Copy a msg/CalibrateStatus message.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source message pointer.
 * \param[out] output The target message pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer is null
 *   or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_genie_msgs
bool
genie_msgs__msg__CalibrateStatus__copy(
  const genie_msgs__msg__CalibrateStatus * input,
  genie_msgs__msg__CalibrateStatus * output);

/// Initialize array of msg/CalibrateStatus messages.
/**
 * It allocates the memory for the number of elements and calls
 * genie_msgs__msg__CalibrateStatus__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_genie_msgs
bool
genie_msgs__msg__CalibrateStatus__Sequence__init(genie_msgs__msg__CalibrateStatus__Sequence * array, size_t size);

/// Finalize array of msg/CalibrateStatus messages.
/**
 * It calls
 * genie_msgs__msg__CalibrateStatus__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_genie_msgs
void
genie_msgs__msg__CalibrateStatus__Sequence__fini(genie_msgs__msg__CalibrateStatus__Sequence * array);

/// Create array of msg/CalibrateStatus messages.
/**
 * It allocates the memory for the array and calls
 * genie_msgs__msg__CalibrateStatus__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_genie_msgs
genie_msgs__msg__CalibrateStatus__Sequence *
genie_msgs__msg__CalibrateStatus__Sequence__create(size_t size);

/// Destroy array of msg/CalibrateStatus messages.
/**
 * It calls
 * genie_msgs__msg__CalibrateStatus__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_genie_msgs
void
genie_msgs__msg__CalibrateStatus__Sequence__destroy(genie_msgs__msg__CalibrateStatus__Sequence * array);

/// Check for msg/CalibrateStatus message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_genie_msgs
bool
genie_msgs__msg__CalibrateStatus__Sequence__are_equal(const genie_msgs__msg__CalibrateStatus__Sequence * lhs, const genie_msgs__msg__CalibrateStatus__Sequence * rhs);

/// Copy an array of msg/CalibrateStatus messages.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source array pointer.
 * \param[out] output The target array pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer
 *   is null or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_genie_msgs
bool
genie_msgs__msg__CalibrateStatus__Sequence__copy(
  const genie_msgs__msg__CalibrateStatus__Sequence * input,
  genie_msgs__msg__CalibrateStatus__Sequence * output);

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__MSG__DETAIL__CALIBRATE_STATUS__FUNCTIONS_H_
