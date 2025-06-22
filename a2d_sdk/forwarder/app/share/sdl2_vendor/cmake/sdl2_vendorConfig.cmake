# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_sdl2_vendor_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED sdl2_vendor_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(sdl2_vendor_FOUND FALSE)
  elseif(NOT sdl2_vendor_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(sdl2_vendor_FOUND FALSE)
  endif()
  return()
endif()
set(_sdl2_vendor_CONFIG_INCLUDED TRUE)

# output package information
if(NOT sdl2_vendor_FIND_QUIETLY)
  message(STATUS "Found sdl2_vendor: 3.3.0 (${sdl2_vendor_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'sdl2_vendor' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT ${sdl2_vendor_DEPRECATED_QUIET})
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(sdl2_vendor_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "sdl2_vendor-extras.cmake")
foreach(_extra ${_extras})
  include("${sdl2_vendor_DIR}/${_extra}")
endforeach()
