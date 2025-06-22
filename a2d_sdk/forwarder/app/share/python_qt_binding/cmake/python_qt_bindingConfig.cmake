# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_python_qt_binding_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED python_qt_binding_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(python_qt_binding_FOUND FALSE)
  elseif(NOT python_qt_binding_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(python_qt_binding_FOUND FALSE)
  endif()
  return()
endif()
set(_python_qt_binding_CONFIG_INCLUDED TRUE)

# output package information
if(NOT python_qt_binding_FIND_QUIETLY)
  message(STATUS "Found python_qt_binding: 1.1.2 (${python_qt_binding_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'python_qt_binding' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT ${python_qt_binding_DEPRECATED_QUIET})
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(python_qt_binding_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "")
foreach(_extra ${_extras})
  include("${python_qt_binding_DIR}/${_extra}")
endforeach()
