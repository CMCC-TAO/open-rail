# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_rosidl_parser_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED rosidl_parser_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(rosidl_parser_FOUND FALSE)
  elseif(NOT rosidl_parser_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(rosidl_parser_FOUND FALSE)
  endif()
  return()
endif()
set(_rosidl_parser_CONFIG_INCLUDED TRUE)

# output package information
if(NOT rosidl_parser_FIND_QUIETLY)
  message(STATUS "Found rosidl_parser: 3.1.5 (${rosidl_parser_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'rosidl_parser' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT ${rosidl_parser_DEPRECATED_QUIET})
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(rosidl_parser_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "")
foreach(_extra ${_extras})
  include("${rosidl_parser_DIR}/${_extra}")
endforeach()
