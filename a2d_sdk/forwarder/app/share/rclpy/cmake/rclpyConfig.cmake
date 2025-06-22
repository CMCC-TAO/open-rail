# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_rclpy_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED rclpy_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(rclpy_FOUND FALSE)
  elseif(NOT rclpy_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(rclpy_FOUND FALSE)
  endif()
  return()
endif()
set(_rclpy_CONFIG_INCLUDED TRUE)

# output package information
if(NOT rclpy_FIND_QUIETLY)
  message(STATUS "Found rclpy: 3.3.14 (${rclpy_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'rclpy' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT ${rclpy_DEPRECATED_QUIET})
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(rclpy_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "")
foreach(_extra ${_extras})
  include("${rclpy_DIR}/${_extra}")
endforeach()
