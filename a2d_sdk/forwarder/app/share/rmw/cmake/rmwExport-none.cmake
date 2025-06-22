#----------------------------------------------------------------
# Generated CMake target import file for configuration "None".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "rmw::rmw" for configuration "None"
set_property(TARGET rmw::rmw APPEND PROPERTY IMPORTED_CONFIGURATIONS NONE)
set_target_properties(rmw::rmw PROPERTIES
  IMPORTED_LOCATION_NONE "${_IMPORT_PREFIX}/lib/librmw.so"
  IMPORTED_SONAME_NONE "librmw.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS rmw::rmw )
list(APPEND _IMPORT_CHECK_FILES_FOR_rmw::rmw "${_IMPORT_PREFIX}/lib/librmw.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
