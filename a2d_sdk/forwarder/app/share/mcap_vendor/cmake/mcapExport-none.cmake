#----------------------------------------------------------------
# Generated CMake target import file for configuration "None".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "mcap_vendor::mcap" for configuration "None"
set_property(TARGET mcap_vendor::mcap APPEND PROPERTY IMPORTED_CONFIGURATIONS NONE)
set_target_properties(mcap_vendor::mcap PROPERTIES
  IMPORTED_LOCATION_NONE "${_IMPORT_PREFIX}/lib/libmcap.so"
  IMPORTED_SONAME_NONE "libmcap.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS mcap_vendor::mcap )
list(APPEND _IMPORT_CHECK_FILES_FOR_mcap_vendor::mcap "${_IMPORT_PREFIX}/lib/libmcap.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
