# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_spdlog_vendor_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED spdlog_vendor_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(spdlog_vendor_FOUND FALSE)
  elseif(NOT spdlog_vendor_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(spdlog_vendor_FOUND FALSE)
  endif()
  return()
endif()
set(_spdlog_vendor_CONFIG_INCLUDED TRUE)

# output package information
if(NOT spdlog_vendor_FIND_QUIETLY)
  message(STATUS "Found spdlog_vendor: 1.3.1 (${spdlog_vendor_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'spdlog_vendor' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT ${spdlog_vendor_DEPRECATED_QUIET})
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(spdlog_vendor_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "")
foreach(_extra ${_extras})
  include("${spdlog_vendor_DIR}/${_extra}")
endforeach()
