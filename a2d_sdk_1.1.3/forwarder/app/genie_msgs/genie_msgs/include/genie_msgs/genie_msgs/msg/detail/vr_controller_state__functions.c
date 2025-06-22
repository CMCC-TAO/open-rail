// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from genie_msgs:msg/VRControllerState.idl
// generated code does not contain a copyright notice
#include "genie_msgs/msg/detail/vr_controller_state__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `name`
#include "rosidl_runtime_c/string_functions.h"
// Member `position`
#include "geometry_msgs/msg/detail/vector3__functions.h"
// Member `orientation`
#include "geometry_msgs/msg/detail/quaternion__functions.h"

bool
genie_msgs__msg__VRControllerState__init(genie_msgs__msg__VRControllerState * msg)
{
  if (!msg) {
    return false;
  }
  // name
  if (!rosidl_runtime_c__String__init(&msg->name)) {
    genie_msgs__msg__VRControllerState__fini(msg);
    return false;
  }
  // id
  // key_one
  // key_two
  // hand_trig
  // index_trig
  // axis_x
  // axis_y
  // axis_click
  // position
  if (!geometry_msgs__msg__Vector3__init(&msg->position)) {
    genie_msgs__msg__VRControllerState__fini(msg);
    return false;
  }
  // orientation
  if (!geometry_msgs__msg__Quaternion__init(&msg->orientation)) {
    genie_msgs__msg__VRControllerState__fini(msg);
    return false;
  }
  return true;
}

void
genie_msgs__msg__VRControllerState__fini(genie_msgs__msg__VRControllerState * msg)
{
  if (!msg) {
    return;
  }
  // name
  rosidl_runtime_c__String__fini(&msg->name);
  // id
  // key_one
  // key_two
  // hand_trig
  // index_trig
  // axis_x
  // axis_y
  // axis_click
  // position
  geometry_msgs__msg__Vector3__fini(&msg->position);
  // orientation
  geometry_msgs__msg__Quaternion__fini(&msg->orientation);
}

bool
genie_msgs__msg__VRControllerState__are_equal(const genie_msgs__msg__VRControllerState * lhs, const genie_msgs__msg__VRControllerState * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // name
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->name), &(rhs->name)))
  {
    return false;
  }
  // id
  if (lhs->id != rhs->id) {
    return false;
  }
  // key_one
  if (lhs->key_one != rhs->key_one) {
    return false;
  }
  // key_two
  if (lhs->key_two != rhs->key_two) {
    return false;
  }
  // hand_trig
  if (lhs->hand_trig != rhs->hand_trig) {
    return false;
  }
  // index_trig
  if (lhs->index_trig != rhs->index_trig) {
    return false;
  }
  // axis_x
  if (lhs->axis_x != rhs->axis_x) {
    return false;
  }
  // axis_y
  if (lhs->axis_y != rhs->axis_y) {
    return false;
  }
  // axis_click
  if (lhs->axis_click != rhs->axis_click) {
    return false;
  }
  // position
  if (!geometry_msgs__msg__Vector3__are_equal(
      &(lhs->position), &(rhs->position)))
  {
    return false;
  }
  // orientation
  if (!geometry_msgs__msg__Quaternion__are_equal(
      &(lhs->orientation), &(rhs->orientation)))
  {
    return false;
  }
  return true;
}

bool
genie_msgs__msg__VRControllerState__copy(
  const genie_msgs__msg__VRControllerState * input,
  genie_msgs__msg__VRControllerState * output)
{
  if (!input || !output) {
    return false;
  }
  // name
  if (!rosidl_runtime_c__String__copy(
      &(input->name), &(output->name)))
  {
    return false;
  }
  // id
  output->id = input->id;
  // key_one
  output->key_one = input->key_one;
  // key_two
  output->key_two = input->key_two;
  // hand_trig
  output->hand_trig = input->hand_trig;
  // index_trig
  output->index_trig = input->index_trig;
  // axis_x
  output->axis_x = input->axis_x;
  // axis_y
  output->axis_y = input->axis_y;
  // axis_click
  output->axis_click = input->axis_click;
  // position
  if (!geometry_msgs__msg__Vector3__copy(
      &(input->position), &(output->position)))
  {
    return false;
  }
  // orientation
  if (!geometry_msgs__msg__Quaternion__copy(
      &(input->orientation), &(output->orientation)))
  {
    return false;
  }
  return true;
}

genie_msgs__msg__VRControllerState *
genie_msgs__msg__VRControllerState__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__VRControllerState * msg = (genie_msgs__msg__VRControllerState *)allocator.allocate(sizeof(genie_msgs__msg__VRControllerState), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(genie_msgs__msg__VRControllerState));
  bool success = genie_msgs__msg__VRControllerState__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
genie_msgs__msg__VRControllerState__destroy(genie_msgs__msg__VRControllerState * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    genie_msgs__msg__VRControllerState__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
genie_msgs__msg__VRControllerState__Sequence__init(genie_msgs__msg__VRControllerState__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__VRControllerState * data = NULL;

  if (size) {
    data = (genie_msgs__msg__VRControllerState *)allocator.zero_allocate(size, sizeof(genie_msgs__msg__VRControllerState), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = genie_msgs__msg__VRControllerState__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        genie_msgs__msg__VRControllerState__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
genie_msgs__msg__VRControllerState__Sequence__fini(genie_msgs__msg__VRControllerState__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      genie_msgs__msg__VRControllerState__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

genie_msgs__msg__VRControllerState__Sequence *
genie_msgs__msg__VRControllerState__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__VRControllerState__Sequence * array = (genie_msgs__msg__VRControllerState__Sequence *)allocator.allocate(sizeof(genie_msgs__msg__VRControllerState__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = genie_msgs__msg__VRControllerState__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
genie_msgs__msg__VRControllerState__Sequence__destroy(genie_msgs__msg__VRControllerState__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    genie_msgs__msg__VRControllerState__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
genie_msgs__msg__VRControllerState__Sequence__are_equal(const genie_msgs__msg__VRControllerState__Sequence * lhs, const genie_msgs__msg__VRControllerState__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!genie_msgs__msg__VRControllerState__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
genie_msgs__msg__VRControllerState__Sequence__copy(
  const genie_msgs__msg__VRControllerState__Sequence * input,
  genie_msgs__msg__VRControllerState__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(genie_msgs__msg__VRControllerState);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    genie_msgs__msg__VRControllerState * data =
      (genie_msgs__msg__VRControllerState *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!genie_msgs__msg__VRControllerState__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          genie_msgs__msg__VRControllerState__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!genie_msgs__msg__VRControllerState__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
