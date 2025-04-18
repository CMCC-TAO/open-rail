// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from genie_msgs:msg/MocapNetwork.idl
// generated code does not contain a copyright notice
#include "genie_msgs/msg/detail/mocap_network__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/detail/header__functions.h"
// Member `device_name`
// Member `ip_address`
// Member `remote_ip_address`
#include "rosidl_runtime_c/string_functions.h"

bool
genie_msgs__msg__MocapNetwork__init(genie_msgs__msg__MocapNetwork * msg)
{
  if (!msg) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__init(&msg->header)) {
    genie_msgs__msg__MocapNetwork__fini(msg);
    return false;
  }
  // device_name
  if (!rosidl_runtime_c__String__init(&msg->device_name)) {
    genie_msgs__msg__MocapNetwork__fini(msg);
    return false;
  }
  // is_connected
  // packet_loss_rate
  // latency
  // frequency
  // ip_address
  if (!rosidl_runtime_c__String__init(&msg->ip_address)) {
    genie_msgs__msg__MocapNetwork__fini(msg);
    return false;
  }
  // remote_ip_address
  if (!rosidl_runtime_c__String__init(&msg->remote_ip_address)) {
    genie_msgs__msg__MocapNetwork__fini(msg);
    return false;
  }
  return true;
}

void
genie_msgs__msg__MocapNetwork__fini(genie_msgs__msg__MocapNetwork * msg)
{
  if (!msg) {
    return;
  }
  // header
  std_msgs__msg__Header__fini(&msg->header);
  // device_name
  rosidl_runtime_c__String__fini(&msg->device_name);
  // is_connected
  // packet_loss_rate
  // latency
  // frequency
  // ip_address
  rosidl_runtime_c__String__fini(&msg->ip_address);
  // remote_ip_address
  rosidl_runtime_c__String__fini(&msg->remote_ip_address);
}

bool
genie_msgs__msg__MocapNetwork__are_equal(const genie_msgs__msg__MocapNetwork * lhs, const genie_msgs__msg__MocapNetwork * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__are_equal(
      &(lhs->header), &(rhs->header)))
  {
    return false;
  }
  // device_name
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->device_name), &(rhs->device_name)))
  {
    return false;
  }
  // is_connected
  if (lhs->is_connected != rhs->is_connected) {
    return false;
  }
  // packet_loss_rate
  if (lhs->packet_loss_rate != rhs->packet_loss_rate) {
    return false;
  }
  // latency
  if (lhs->latency != rhs->latency) {
    return false;
  }
  // frequency
  if (lhs->frequency != rhs->frequency) {
    return false;
  }
  // ip_address
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->ip_address), &(rhs->ip_address)))
  {
    return false;
  }
  // remote_ip_address
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->remote_ip_address), &(rhs->remote_ip_address)))
  {
    return false;
  }
  return true;
}

bool
genie_msgs__msg__MocapNetwork__copy(
  const genie_msgs__msg__MocapNetwork * input,
  genie_msgs__msg__MocapNetwork * output)
{
  if (!input || !output) {
    return false;
  }
  // header
  if (!std_msgs__msg__Header__copy(
      &(input->header), &(output->header)))
  {
    return false;
  }
  // device_name
  if (!rosidl_runtime_c__String__copy(
      &(input->device_name), &(output->device_name)))
  {
    return false;
  }
  // is_connected
  output->is_connected = input->is_connected;
  // packet_loss_rate
  output->packet_loss_rate = input->packet_loss_rate;
  // latency
  output->latency = input->latency;
  // frequency
  output->frequency = input->frequency;
  // ip_address
  if (!rosidl_runtime_c__String__copy(
      &(input->ip_address), &(output->ip_address)))
  {
    return false;
  }
  // remote_ip_address
  if (!rosidl_runtime_c__String__copy(
      &(input->remote_ip_address), &(output->remote_ip_address)))
  {
    return false;
  }
  return true;
}

genie_msgs__msg__MocapNetwork *
genie_msgs__msg__MocapNetwork__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__MocapNetwork * msg = (genie_msgs__msg__MocapNetwork *)allocator.allocate(sizeof(genie_msgs__msg__MocapNetwork), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(genie_msgs__msg__MocapNetwork));
  bool success = genie_msgs__msg__MocapNetwork__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
genie_msgs__msg__MocapNetwork__destroy(genie_msgs__msg__MocapNetwork * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    genie_msgs__msg__MocapNetwork__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
genie_msgs__msg__MocapNetwork__Sequence__init(genie_msgs__msg__MocapNetwork__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__MocapNetwork * data = NULL;

  if (size) {
    data = (genie_msgs__msg__MocapNetwork *)allocator.zero_allocate(size, sizeof(genie_msgs__msg__MocapNetwork), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = genie_msgs__msg__MocapNetwork__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        genie_msgs__msg__MocapNetwork__fini(&data[i - 1]);
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
genie_msgs__msg__MocapNetwork__Sequence__fini(genie_msgs__msg__MocapNetwork__Sequence * array)
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
      genie_msgs__msg__MocapNetwork__fini(&array->data[i]);
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

genie_msgs__msg__MocapNetwork__Sequence *
genie_msgs__msg__MocapNetwork__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  genie_msgs__msg__MocapNetwork__Sequence * array = (genie_msgs__msg__MocapNetwork__Sequence *)allocator.allocate(sizeof(genie_msgs__msg__MocapNetwork__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = genie_msgs__msg__MocapNetwork__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
genie_msgs__msg__MocapNetwork__Sequence__destroy(genie_msgs__msg__MocapNetwork__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    genie_msgs__msg__MocapNetwork__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
genie_msgs__msg__MocapNetwork__Sequence__are_equal(const genie_msgs__msg__MocapNetwork__Sequence * lhs, const genie_msgs__msg__MocapNetwork__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!genie_msgs__msg__MocapNetwork__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
genie_msgs__msg__MocapNetwork__Sequence__copy(
  const genie_msgs__msg__MocapNetwork__Sequence * input,
  genie_msgs__msg__MocapNetwork__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(genie_msgs__msg__MocapNetwork);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    genie_msgs__msg__MocapNetwork * data =
      (genie_msgs__msg__MocapNetwork *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!genie_msgs__msg__MocapNetwork__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          genie_msgs__msg__MocapNetwork__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!genie_msgs__msg__MocapNetwork__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
