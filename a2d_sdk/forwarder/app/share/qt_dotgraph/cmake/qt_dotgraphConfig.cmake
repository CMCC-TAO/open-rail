# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_qt_dotgraph_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED qt_dotgraph_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(qt_dotgraph_FOUND FALSE)
  elseif(NOT qt_dotgraph_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(qt_dotgraph_FOUND FALSE)
  endif()
  return()
endif()
set(_qt_dotgraph_CONFIG_INCLUDED TRUE)

# output package information
if(NOT qt_dotgraph_FIND_QUIETLY)
  message(STATUS "Found qt_dotgraph: 2.2.3 (${qt_dotgraph_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'qt_dotgraph' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT ${qt_dotgraph_DEPRECATED_QUIET})
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(qt_dotgraph_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "")
foreach(_extra ${_extras})
  include("${qt_dotgraph_DIR}/${_extra}")
endforeach()
