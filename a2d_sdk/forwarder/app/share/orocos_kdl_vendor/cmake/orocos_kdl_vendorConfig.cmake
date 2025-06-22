# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_orocos_kdl_vendor_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED orocos_kdl_vendor_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(orocos_kdl_vendor_FOUND FALSE)
  elseif(NOT orocos_kdl_vendor_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(orocos_kdl_vendor_FOUND FALSE)
  endif()
  return()
endif()
set(_orocos_kdl_vendor_CONFIG_INCLUDED TRUE)

# output package information
if(NOT orocos_kdl_vendor_FIND_QUIETLY)
  message(STATUS "Found orocos_kdl_vendor: 0.2.5 (${orocos_kdl_vendor_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'orocos_kdl_vendor' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT ${orocos_kdl_vendor_DEPRECATED_QUIET})
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(orocos_kdl_vendor_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "orocos_kdl_vendor-extras.cmake")
foreach(_extra ${_extras})
  include("${orocos_kdl_vendor_DIR}/${_extra}")
endforeach()
