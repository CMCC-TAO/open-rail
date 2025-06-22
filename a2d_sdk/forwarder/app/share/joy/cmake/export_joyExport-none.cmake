#----------------------------------------------------------------
# Generated CMake target import file for configuration "None".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "joy::joy" for configuration "None"
set_property(TARGET joy::joy APPEND PROPERTY IMPORTED_CONFIGURATIONS NONE)
set_target_properties(joy::joy PROPERTIES
  IMPORTED_LOCATION_NONE "${_IMPORT_PREFIX}/lib/libjoy.so"
  IMPORTED_SONAME_NONE "libjoy.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS joy::joy )
list(APPEND _IMPORT_CHECK_FILES_FOR_joy::joy "${_IMPORT_PREFIX}/lib/libjoy.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
