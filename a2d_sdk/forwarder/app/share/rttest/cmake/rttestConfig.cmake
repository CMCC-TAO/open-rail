# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_rttest_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED rttest_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(rttest_FOUND FALSE)
  elseif(NOT rttest_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(rttest_FOUND FALSE)
  endif()
  return()
endif()
set(_rttest_CONFIG_INCLUDED TRUE)

# output package information
if(NOT rttest_FIND_QUIETLY)
  message(STATUS "Found rttest: 0.13.0 (${rttest_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'rttest' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT ${rttest_DEPRECATED_QUIET})
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(rttest_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "ament_cmake_export_targets-extras.cmake")
foreach(_extra ${_extras})
  include("${rttest_DIR}/${_extra}")
endforeach()
