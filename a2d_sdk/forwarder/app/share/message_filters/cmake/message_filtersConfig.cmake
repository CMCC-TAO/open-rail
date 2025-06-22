# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_message_filters_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED message_filters_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(message_filters_FOUND FALSE)
  elseif(NOT message_filters_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(message_filters_FOUND FALSE)
  endif()
  return()
endif()
set(_message_filters_CONFIG_INCLUDED TRUE)

# output package information
if(NOT message_filters_FIND_QUIETLY)
  message(STATUS "Found message_filters: 4.3.5 (${message_filters_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'message_filters' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT ${message_filters_DEPRECATED_QUIET})
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(message_filters_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "ament_cmake_export_include_directories-extras.cmake;ament_cmake_export_libraries-extras.cmake;ament_cmake_export_targets-extras.cmake;ament_cmake_export_dependencies-extras.cmake")
foreach(_extra ${_extras})
  include("${message_filters_DIR}/${_extra}")
endforeach()
