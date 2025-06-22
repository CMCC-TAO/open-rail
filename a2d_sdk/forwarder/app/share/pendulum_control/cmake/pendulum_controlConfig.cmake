# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_pendulum_control_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED pendulum_control_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(pendulum_control_FOUND FALSE)
  elseif(NOT pendulum_control_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(pendulum_control_FOUND FALSE)
  endif()
  return()
endif()
set(_pendulum_control_CONFIG_INCLUDED TRUE)

# output package information
if(NOT pendulum_control_FIND_QUIETLY)
  message(STATUS "Found pendulum_control: 0.20.5 (${pendulum_control_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'pendulum_control' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT ${pendulum_control_DEPRECATED_QUIET})
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(pendulum_control_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "")
foreach(_extra ${_extras})
  include("${pendulum_control_DIR}/${_extra}")
endforeach()
