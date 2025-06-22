# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_yaml_cpp_vendor_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED yaml_cpp_vendor_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(yaml_cpp_vendor_FOUND FALSE)
  elseif(NOT yaml_cpp_vendor_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(yaml_cpp_vendor_FOUND FALSE)
  endif()
  return()
endif()
set(_yaml_cpp_vendor_CONFIG_INCLUDED TRUE)

# output package information
if(NOT yaml_cpp_vendor_FIND_QUIETLY)
  message(STATUS "Found yaml_cpp_vendor: 8.0.2 (${yaml_cpp_vendor_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'yaml_cpp_vendor' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT ${yaml_cpp_vendor_DEPRECATED_QUIET})
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(yaml_cpp_vendor_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "yaml_cpp_vendor-extras.cmake")
foreach(_extra ${_extras})
  include("${yaml_cpp_vendor_DIR}/${_extra}")
endforeach()
