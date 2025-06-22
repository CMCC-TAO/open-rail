# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_pluginlib_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED pluginlib_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(pluginlib_FOUND FALSE)
  elseif(NOT pluginlib_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(pluginlib_FOUND FALSE)
  endif()
  return()
endif()
set(_pluginlib_CONFIG_INCLUDED TRUE)

# output package information
if(NOT pluginlib_FIND_QUIETLY)
  message(STATUS "Found pluginlib: 5.1.0 (${pluginlib_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'pluginlib' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT ${pluginlib_DEPRECATED_QUIET})
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(pluginlib_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "pluginlib-extras.cmake;ament_cmake_export_dependencies-extras.cmake;ament_cmake_export_targets-extras.cmake")
foreach(_extra ${_extras})
  include("${pluginlib_DIR}/${_extra}")
endforeach()
