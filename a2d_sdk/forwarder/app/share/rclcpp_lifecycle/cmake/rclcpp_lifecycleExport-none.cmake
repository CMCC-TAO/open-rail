#----------------------------------------------------------------
# Generated CMake target import file for configuration "None".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "rclcpp_lifecycle::rclcpp_lifecycle" for configuration "None"
set_property(TARGET rclcpp_lifecycle::rclcpp_lifecycle APPEND PROPERTY IMPORTED_CONFIGURATIONS NONE)
set_target_properties(rclcpp_lifecycle::rclcpp_lifecycle PROPERTIES
  IMPORTED_LOCATION_NONE "${_IMPORT_PREFIX}/lib/librclcpp_lifecycle.so"
  IMPORTED_SONAME_NONE "librclcpp_lifecycle.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS rclcpp_lifecycle::rclcpp_lifecycle )
list(APPEND _IMPORT_CHECK_FILES_FOR_rclcpp_lifecycle::rclcpp_lifecycle "${_IMPORT_PREFIX}/lib/librclcpp_lifecycle.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
