# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_kdl_parser_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED kdl_parser_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(kdl_parser_FOUND FALSE)
  elseif(NOT kdl_parser_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(kdl_parser_FOUND FALSE)
  endif()
  return()
endif()
set(_kdl_parser_CONFIG_INCLUDED TRUE)

# output package information
if(NOT kdl_parser_FIND_QUIETLY)
  message(STATUS "Found kdl_parser: 2.6.4 (${kdl_parser_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'kdl_parser' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT ${kdl_parser_DEPRECATED_QUIET})
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(kdl_parser_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "ament_cmake_export_dependencies-extras.cmake;ament_cmake_export_targets-extras.cmake")
foreach(_extra ${_extras})
  include("${kdl_parser_DIR}/${_extra}")
endforeach()
