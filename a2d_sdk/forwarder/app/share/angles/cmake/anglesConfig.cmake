# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_angles_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED angles_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(angles_FOUND FALSE)
  elseif(NOT angles_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(angles_FOUND FALSE)
  endif()
  return()
endif()
set(_angles_CONFIG_INCLUDED TRUE)

# output package information
if(NOT angles_FIND_QUIETLY)
  message(STATUS "Found angles: 1.15.0 (${angles_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'angles' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT ${angles_DEPRECATED_QUIET})
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(angles_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "ament_cmake_export_include_directories-extras.cmake;ament_cmake_export_targets-extras.cmake")
foreach(_extra ${_extras})
  include("${angles_DIR}/${_extra}")
endforeach()
