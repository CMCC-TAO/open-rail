#----------------------------------------------------------------
# Generated CMake target import file for configuration "None".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "rclcpp::rclcpp" for configuration "None"
set_property(TARGET rclcpp::rclcpp APPEND PROPERTY IMPORTED_CONFIGURATIONS NONE)
set_target_properties(rclcpp::rclcpp PROPERTIES
  IMPORTED_LOCATION_NONE "${_IMPORT_PREFIX}/lib/librclcpp.so"
  IMPORTED_SONAME_NONE "librclcpp.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS rclcpp::rclcpp )
list(APPEND _IMPORT_CHECK_FILES_FOR_rclcpp::rclcpp "${_IMPORT_PREFIX}/lib/librclcpp.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
