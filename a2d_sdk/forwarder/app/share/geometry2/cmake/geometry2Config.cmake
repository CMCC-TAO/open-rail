# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_geometry2_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED geometry2_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(geometry2_FOUND FALSE)
  elseif(NOT geometry2_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(geometry2_FOUND FALSE)
  endif()
  return()
endif()
set(_geometry2_CONFIG_INCLUDED TRUE)

# output package information
if(NOT geometry2_FIND_QUIETLY)
  message(STATUS "Found geometry2: 0.25.8 (${geometry2_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'geometry2' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT ${geometry2_DEPRECATED_QUIET})
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(geometry2_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "")
foreach(_extra ${_extras})
  include("${geometry2_DIR}/${_extra}")
endforeach()
