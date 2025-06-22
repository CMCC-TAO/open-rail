# generated from ament_cmake_export_include_directories/cmake/ament_cmake_export_include_directories-extras.cmake.in

set(_exported_include_dirs "${quality_of_service_demo_cpp_DIR}/../../../include/quality_of_service_demo_cpp")

# append include directories to quality_of_service_demo_cpp_INCLUDE_DIRS
# warn about not existing paths
if(NOT _exported_include_dirs STREQUAL "")
  find_package(ament_cmake_core QUIET REQUIRED)
  foreach(_exported_include_dir ${_exported_include_dirs})
    if(NOT IS_DIRECTORY "${_exported_include_dir}")
      message(WARNING "Package 'quality_of_service_demo_cpp' exports the include directory '${_exported_include_dir}' which doesn't exist")
    endif()
    normalize_path(_exported_include_dir "${_exported_include_dir}")
    list(APPEND quality_of_service_demo_cpp_INCLUDE_DIRS "${_exported_include_dir}")
  endforeach()
endif()
