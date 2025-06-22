# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_resource_retriever_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED resource_retriever_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(resource_retriever_FOUND FALSE)
  elseif(NOT resource_retriever_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(resource_retriever_FOUND FALSE)
  endif()
  return()
endif()
set(_resource_retriever_CONFIG_INCLUDED TRUE)

# output package information
if(NOT resource_retriever_FIND_QUIETLY)
  message(STATUS "Found resource_retriever: 3.1.2 (${resource_retriever_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'resource_retriever' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT ${resource_retriever_DEPRECATED_QUIET})
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(resource_retriever_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "ament_cmake_export_include_directories-extras.cmake;ament_cmake_export_targets-extras.cmake;ament_cmake_export_dependencies-extras.cmake")
foreach(_extra ${_extras})
  include("${resource_retriever_DIR}/${_extra}")
endforeach()
