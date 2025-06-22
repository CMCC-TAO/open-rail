# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_actionlib_msgs_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED actionlib_msgs_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(actionlib_msgs_FOUND FALSE)
  elseif(NOT actionlib_msgs_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(actionlib_msgs_FOUND FALSE)
  endif()
  return()
endif()
set(_actionlib_msgs_CONFIG_INCLUDED TRUE)

# output package information
if(NOT actionlib_msgs_FIND_QUIETLY)
  message(STATUS "Found actionlib_msgs: 4.2.4 (${actionlib_msgs_DIR})")
endif()

# warn when using a deprecated package
if(NOT "This package will be removed in a future ROS distro, once the ROS 1 bridge supports actions." STREQUAL "")
  set(_msg "Package 'actionlib_msgs' is deprecated")
  # append custom deprecation text if available
  if(NOT "This package will be removed in a future ROS distro, once the ROS 1 bridge supports actions." STREQUAL "TRUE")
    set(_msg "${_msg} (This package will be removed in a future ROS distro, once the ROS 1 bridge supports actions.)")
  endif()
  # optionally quiet the deprecation message
  if(NOT ${actionlib_msgs_DEPRECATED_QUIET})
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(actionlib_msgs_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "rosidl_cmake-extras.cmake;ament_cmake_export_dependencies-extras.cmake;ament_cmake_export_include_directories-extras.cmake;ament_cmake_export_libraries-extras.cmake;ament_cmake_export_targets-extras.cmake;rosidl_cmake_export_typesupport_targets-extras.cmake;rosidl_cmake_export_typesupport_libraries-extras.cmake")
foreach(_extra ${_extras})
  include("${actionlib_msgs_DIR}/${_extra}")
endforeach()
