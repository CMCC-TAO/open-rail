# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_joy_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED joy_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(joy_FOUND FALSE)
  elseif(NOT joy_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(joy_FOUND FALSE)
  endif()
  return()
endif()
set(_joy_CONFIG_INCLUDED TRUE)

# output package information
if(NOT joy_FIND_QUIETLY)
  message(STATUS "Found joy: 3.3.0 (${joy_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'joy' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT ${joy_DEPRECATED_QUIET})
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(joy_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "ament_cmake_export_targets-extras.cmake;ament_cmake_export_dependencies-extras.cmake")
foreach(_extra ${_extras})
  include("${joy_DIR}/${_extra}")
endforeach()
