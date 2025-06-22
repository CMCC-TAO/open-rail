# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_rqt_image_view_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED rqt_image_view_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(rqt_image_view_FOUND FALSE)
  elseif(NOT rqt_image_view_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(rqt_image_view_FOUND FALSE)
  endif()
  return()
endif()
set(_rqt_image_view_CONFIG_INCLUDED TRUE)

# output package information
if(NOT rqt_image_view_FIND_QUIETLY)
  message(STATUS "Found rqt_image_view: 1.2.0 (${rqt_image_view_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'rqt_image_view' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT ${rqt_image_view_DEPRECATED_QUIET})
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(rqt_image_view_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "ament_cmake_export_include_directories-extras.cmake;ament_cmake_export_libraries-extras.cmake;ament_cmake_export_targets-extras.cmake")
foreach(_extra ${_extras})
  include("${rqt_image_view_DIR}/${_extra}")
endforeach()
