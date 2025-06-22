#----------------------------------------------------------------
# Generated CMake target import file for configuration "None".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "rcl_interfaces::rcl_interfaces__rosidl_generator_c" for configuration "None"
set_property(TARGET rcl_interfaces::rcl_interfaces__rosidl_generator_c APPEND PROPERTY IMPORTED_CONFIGURATIONS NONE)
set_target_properties(rcl_interfaces::rcl_interfaces__rosidl_generator_c PROPERTIES
  IMPORTED_LOCATION_NONE "${_IMPORT_PREFIX}/lib/librcl_interfaces__rosidl_generator_c.so"
  IMPORTED_SONAME_NONE "librcl_interfaces__rosidl_generator_c.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS rcl_interfaces::rcl_interfaces__rosidl_generator_c )
list(APPEND _IMPORT_CHECK_FILES_FOR_rcl_interfaces::rcl_interfaces__rosidl_generator_c "${_IMPORT_PREFIX}/lib/librcl_interfaces__rosidl_generator_c.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
