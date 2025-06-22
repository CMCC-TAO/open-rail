#----------------------------------------------------------------
# Generated CMake target import file for configuration "None".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "interactive_markers::interactive_markers" for configuration "None"
set_property(TARGET interactive_markers::interactive_markers APPEND PROPERTY IMPORTED_CONFIGURATIONS NONE)
set_target_properties(interactive_markers::interactive_markers PROPERTIES
  IMPORTED_LINK_DEPENDENT_LIBRARIES_NONE "rmw::rmw"
  IMPORTED_LOCATION_NONE "${_IMPORT_PREFIX}/lib/libinteractive_markers.so"
  IMPORTED_SONAME_NONE "libinteractive_markers.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS interactive_markers::interactive_markers )
list(APPEND _IMPORT_CHECK_FILES_FOR_interactive_markers::interactive_markers "${_IMPORT_PREFIX}/lib/libinteractive_markers.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
