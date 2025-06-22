#----------------------------------------------------------------
# Generated CMake target import file for configuration "None".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "rclcpp_components::component_manager" for configuration "None"
set_property(TARGET rclcpp_components::component_manager APPEND PROPERTY IMPORTED_CONFIGURATIONS NONE)
set_target_properties(rclcpp_components::component_manager PROPERTIES
  IMPORTED_LOCATION_NONE "${_IMPORT_PREFIX}/lib/libcomponent_manager.so"
  IMPORTED_SONAME_NONE "libcomponent_manager.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS rclcpp_components::component_manager )
list(APPEND _IMPORT_CHECK_FILES_FOR_rclcpp_components::component_manager "${_IMPORT_PREFIX}/lib/libcomponent_manager.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
