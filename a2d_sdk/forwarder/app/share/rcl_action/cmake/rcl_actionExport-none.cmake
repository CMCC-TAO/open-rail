#----------------------------------------------------------------
# Generated CMake target import file for configuration "None".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "rcl_action::rcl_action" for configuration "None"
set_property(TARGET rcl_action::rcl_action APPEND PROPERTY IMPORTED_CONFIGURATIONS NONE)
set_target_properties(rcl_action::rcl_action PROPERTIES
  IMPORTED_LOCATION_NONE "${_IMPORT_PREFIX}/lib/librcl_action.so"
  IMPORTED_SONAME_NONE "librcl_action.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS rcl_action::rcl_action )
list(APPEND _IMPORT_CHECK_FILES_FOR_rcl_action::rcl_action "${_IMPORT_PREFIX}/lib/librcl_action.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
