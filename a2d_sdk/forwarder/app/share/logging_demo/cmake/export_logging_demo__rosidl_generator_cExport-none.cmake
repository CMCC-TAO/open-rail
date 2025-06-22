#----------------------------------------------------------------
# Generated CMake target import file for configuration "None".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "logging_demo::logging_demo__rosidl_generator_c" for configuration "None"
set_property(TARGET logging_demo::logging_demo__rosidl_generator_c APPEND PROPERTY IMPORTED_CONFIGURATIONS NONE)
set_target_properties(logging_demo::logging_demo__rosidl_generator_c PROPERTIES
  IMPORTED_LOCATION_NONE "${_IMPORT_PREFIX}/lib/liblogging_demo__rosidl_generator_c.so"
  IMPORTED_SONAME_NONE "liblogging_demo__rosidl_generator_c.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS logging_demo::logging_demo__rosidl_generator_c )
list(APPEND _IMPORT_CHECK_FILES_FOR_logging_demo::logging_demo__rosidl_generator_c "${_IMPORT_PREFIX}/lib/liblogging_demo__rosidl_generator_c.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
