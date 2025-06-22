# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_depthimage_to_laserscan_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED depthimage_to_laserscan_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(depthimage_to_laserscan_FOUND FALSE)
  elseif(NOT depthimage_to_laserscan_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(depthimage_to_laserscan_FOUND FALSE)
  endif()
  return()
endif()
set(_depthimage_to_laserscan_CONFIG_INCLUDED TRUE)

# output package information
if(NOT depthimage_to_laserscan_FIND_QUIETLY)
  message(STATUS "Found depthimage_to_laserscan: 2.5.1 (${depthimage_to_laserscan_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'depthimage_to_laserscan' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT ${depthimage_to_laserscan_DEPRECATED_QUIET})
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(depthimage_to_laserscan_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "ament_cmake_export_include_directories-extras.cmake;ament_cmake_export_libraries-extras.cmake;ament_cmake_export_targets-extras.cmake;ament_cmake_export_dependencies-extras.cmake")
foreach(_extra ${_extras})
  include("${depthimage_to_laserscan_DIR}/${_extra}")
endforeach()
