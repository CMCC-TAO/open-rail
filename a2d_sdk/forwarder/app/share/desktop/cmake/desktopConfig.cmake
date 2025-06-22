# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_desktop_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED desktop_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(desktop_FOUND FALSE)
  elseif(NOT desktop_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(desktop_FOUND FALSE)
  endif()
  return()
endif()
set(_desktop_CONFIG_INCLUDED TRUE)

# output package information
if(NOT desktop_FIND_QUIETLY)
  message(STATUS "Found desktop: 0.10.0 (${desktop_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'desktop' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT ${desktop_DEPRECATED_QUIET})
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(desktop_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "")
foreach(_extra ${_extras})
  include("${desktop_DIR}/${_extra}")
endforeach()
