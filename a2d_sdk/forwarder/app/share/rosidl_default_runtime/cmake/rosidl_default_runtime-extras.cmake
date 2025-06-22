# generated from
# rosidl_default_runtime/rosidl_default_runtime-extras.cmake.in

find_package(ament_cmake_core REQUIRED)
ament_index_get_resources(rosidl_runtime_packages "rosidl_runtime_packages")

# find_package() all dependencies (if available)
# and append their DEFINITIONS INCLUDE_DIRS and LIBRARIES variables
# to rosidl_default_runtime_DEFINITIONS , rosidl_default_runtime_INCLUDE_DIRS and
# rosidl_default_runtime_LIBRARIES.
foreach(_dep ${rosidl_runtime_packages})
  find_package("${_dep}" QUIET)
  if(${_dep}_FOUND)
    if(${_dep}_DEFINITIONS)
      list(APPEND rosidl_default_runtime_DEFINITIONS "${${_dep}_DEFINITIONS}")
    endif()
    if(${_dep}_INCLUDE_DIRS)
      list(APPEND rosidl_default_runtime_INCLUDE_DIRS "${${_dep}_INCLUDE_DIRS}")
    endif()
    if(${_dep}_LIBRARIES)
      list(APPEND rosidl_default_runtime_LIBRARIES "${${_dep}_LIBRARIES}")
    endif()
  endif()
endforeach()
