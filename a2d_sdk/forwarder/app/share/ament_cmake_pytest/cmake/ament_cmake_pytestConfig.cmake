# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_ament_cmake_pytest_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED ament_cmake_pytest_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(ament_cmake_pytest_FOUND FALSE)
  elseif(NOT ament_cmake_pytest_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(ament_cmake_pytest_FOUND FALSE)
  endif()
  return()
endif()
set(_ament_cmake_pytest_CONFIG_INCLUDED TRUE)

# output package information
if(NOT ament_cmake_pytest_FIND_QUIETLY)
  message(STATUS "Found ament_cmake_pytest: 1.3.10 (${ament_cmake_pytest_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'ament_cmake_pytest' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT ${ament_cmake_pytest_DEPRECATED_QUIET})
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(ament_cmake_pytest_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "ament_cmake_pytest-extras.cmake")
foreach(_extra ${_extras})
  include("${ament_cmake_pytest_DIR}/${_extra}")
endforeach()
