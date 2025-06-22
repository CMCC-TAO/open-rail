#----------------------------------------------------------------
# Generated CMake target import file for configuration "None".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "rcl_logging_interface::rcl_logging_interface" for configuration "None"
set_property(TARGET rcl_logging_interface::rcl_logging_interface APPEND PROPERTY IMPORTED_CONFIGURATIONS NONE)
set_target_properties(rcl_logging_interface::rcl_logging_interface PROPERTIES
  IMPORTED_LOCATION_NONE "${_IMPORT_PREFIX}/lib/librcl_logging_interface.so"
  IMPORTED_SONAME_NONE "librcl_logging_interface.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS rcl_logging_interface::rcl_logging_interface )
list(APPEND _IMPORT_CHECK_FILES_FOR_rcl_logging_interface::rcl_logging_interface "${_IMPORT_PREFIX}/lib/librcl_logging_interface.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
