# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_libstatistics_collector_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED libstatistics_collector_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(libstatistics_collector_FOUND FALSE)
  elseif(NOT libstatistics_collector_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(libstatistics_collector_FOUND FALSE)
  endif()
  return()
endif()
set(_libstatistics_collector_CONFIG_INCLUDED TRUE)

# output package information
if(NOT libstatistics_collector_FIND_QUIETLY)
  message(STATUS "Found libstatistics_collector: 1.3.2 (${libstatistics_collector_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'libstatistics_collector' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT ${libstatistics_collector_DEPRECATED_QUIET})
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(libstatistics_collector_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "ament_cmake_export_include_directories-extras.cmake;ament_cmake_export_libraries-extras.cmake;ament_cmake_export_targets-extras.cmake;ament_cmake_export_dependencies-extras.cmake;rosidl_cmake-extras.cmake")
foreach(_extra ${_extras})
  include("${libstatistics_collector_DIR}/${_extra}")
endforeach()
