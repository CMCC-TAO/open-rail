// generated from rosidl_generator_c/resource/idl__functions.h.em
// with input from genie_msgs:msg/PeriStatus.idl
// generated code does not contain a copyright notice

#ifndef GENIE_MSGS__MSG__DETAIL__PERI_STATUS__FUNCTIONS_H_
#define GENIE_MSGS__MSG__DETAIL__PERI_STATUS__FUNCTIONS_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stdlib.h>

#include "rosidl_runtime_c/visibility_control.h"
#include "genie_msgs/msg/rosidl_generator_c__visibility_control.h"

#include "genie_msgs/msg/detail/peri_status__struct.h"

/// Initialize msg/PeriStatus message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * genie_msgs__msg__PeriStatus
 * )) before or use
 * genie_msgs__msg__PeriStatus__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_genie_msgs
bool
genie_msgs__msg__PeriStatus__init(genie_msgs__msg__PeriStatus * msg);

/// Finalize msg/PeriStatus message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_genie_msgs
void
genie_msgs__msg__PeriStatus__fini(genie_msgs__msg__PeriStatus * msg);

/// Create msg/PeriStatus message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * genie_msgs__msg__PeriStatus__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_genie_msgs
genie_msgs__msg__PeriStatus *
genie_msgs__msg__PeriStatus__create();

/// Destroy msg/PeriStatus message.
/**
 * It calls
 * genie_msgs__msg__PeriStatus__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_genie_msgs
void
genie_msgs__msg__PeriStatus__destroy(genie_msgs__msg__PeriStatus * msg);

/// Check for msg/PeriStatus message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_genie_msgs
bool
genie_msgs__msg__PeriStatus__are_equal(const genie_msgs__msg__PeriStatus * lhs, const genie_msgs__msg__PeriStatus * rhs);

/// Copy a msg/PeriStatus message.
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
genie_msgs__msg__PeriStatus__copy(
  const genie_msgs__msg__PeriStatus * input,
  genie_msgs__msg__PeriStatus * output);

/// Initialize array of msg/PeriStatus messages.
/**
 * It allocates the memory for the number of elements and calls
 * genie_msgs__msg__PeriStatus__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_genie_msgs
bool
genie_msgs__msg__PeriStatus__Sequence__init(genie_msgs__msg__PeriStatus__Sequence * array, size_t size);

/// Finalize array of msg/PeriStatus messages.
/**
 * It calls
 * genie_msgs__msg__PeriStatus__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_genie_msgs
void
genie_msgs__msg__PeriStatus__Sequence__fini(genie_msgs__msg__PeriStatus__Sequence * array);

/// Create array of msg/PeriStatus messages.
/**
 * It allocates the memory for the array and calls
 * genie_msgs__msg__PeriStatus__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_genie_msgs
genie_msgs__msg__PeriStatus__Sequence *
genie_msgs__msg__PeriStatus__Sequence__create(size_t size);

/// Destroy array of msg/PeriStatus messages.
/**
 * It calls
 * genie_msgs__msg__PeriStatus__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_genie_msgs
void
genie_msgs__msg__PeriStatus__Sequence__destroy(genie_msgs__msg__PeriStatus__Sequence * array);

/// Check for msg/PeriStatus message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_genie_msgs
bool
genie_msgs__msg__PeriStatus__Sequence__are_equal(const genie_msgs__msg__PeriStatus__Sequence * lhs, const genie_msgs__msg__PeriStatus__Sequence * rhs);

/// Copy an array of msg/PeriStatus messages.
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
genie_msgs__msg__PeriStatus__Sequence__copy(
  const genie_msgs__msg__PeriStatus__Sequence * input,
  genie_msgs__msg__PeriStatus__Sequence * output);

#ifdef __cplusplus
}
#endif

#endif  // GENIE_MSGS__MSG__DETAIL__PERI_STATUS__FUNCTIONS_H_
