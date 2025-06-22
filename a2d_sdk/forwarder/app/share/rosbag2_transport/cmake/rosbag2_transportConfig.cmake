# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_rosbag2_transport_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED rosbag2_transport_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(rosbag2_transport_FOUND FALSE)
  elseif(NOT rosbag2_transport_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(rosbag2_transport_FOUND FALSE)
  endif()
  return()
endif()
set(_rosbag2_transport_CONFIG_INCLUDED TRUE)

# output package information
if(NOT rosbag2_transport_FIND_QUIETLY)
  message(STATUS "Found rosbag2_transport: 0.15.12 (${rosbag2_transport_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'rosbag2_transport' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT ${rosbag2_transport_DEPRECATED_QUIET})
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(rosbag2_transport_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "ament_cmake_export_include_directories-extras.cmake;ament_cmake_export_libraries-extras.cmake;ament_cmake_export_targets-extras.cmake;ament_cmake_export_dependencies-extras.cmake")
foreach(_extra ${_extras})
  include("${rosbag2_transport_DIR}/${_extra}")
endforeach()
