#----------------------------------------------------------------
# Generated CMake target import file for configuration "None".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "rttest::rttest" for configuration "None"
set_property(TARGET rttest::rttest APPEND PROPERTY IMPORTED_CONFIGURATIONS NONE)
set_target_properties(rttest::rttest PROPERTIES
  IMPORTED_LOCATION_NONE "${_IMPORT_PREFIX}/lib/librttest.so"
  IMPORTED_SONAME_NONE "librttest.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS rttest::rttest )
list(APPEND _IMPORT_CHECK_FILES_FOR_rttest::rttest "${_IMPORT_PREFIX}/lib/librttest.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
