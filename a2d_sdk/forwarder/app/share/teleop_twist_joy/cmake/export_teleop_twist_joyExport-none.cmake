#----------------------------------------------------------------
# Generated CMake target import file for configuration "None".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "teleop_twist_joy::teleop_twist_joy" for configuration "None"
set_property(TARGET teleop_twist_joy::teleop_twist_joy APPEND PROPERTY IMPORTED_CONFIGURATIONS NONE)
set_target_properties(teleop_twist_joy::teleop_twist_joy PROPERTIES
  IMPORTED_LOCATION_NONE "${_IMPORT_PREFIX}/lib/libteleop_twist_joy.so"
  IMPORTED_SONAME_NONE "libteleop_twist_joy.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS teleop_twist_joy::teleop_twist_joy )
list(APPEND _IMPORT_CHECK_FILES_FOR_teleop_twist_joy::teleop_twist_joy "${_IMPORT_PREFIX}/lib/libteleop_twist_joy.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
