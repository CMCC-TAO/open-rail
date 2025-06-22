#----------------------------------------------------------------
# Generated CMake target import file for configuration "None".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "urdf::urdf" for configuration "None"
set_property(TARGET urdf::urdf APPEND PROPERTY IMPORTED_CONFIGURATIONS NONE)
set_target_properties(urdf::urdf PROPERTIES
  IMPORTED_LOCATION_NONE "${_IMPORT_PREFIX}/lib/liburdf.so"
  IMPORTED_SONAME_NONE "liburdf.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS urdf::urdf )
list(APPEND _IMPORT_CHECK_FILES_FOR_urdf::urdf "${_IMPORT_PREFIX}/lib/liburdf.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
