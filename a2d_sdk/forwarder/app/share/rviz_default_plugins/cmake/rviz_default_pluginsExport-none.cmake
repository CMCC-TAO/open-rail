#----------------------------------------------------------------
# Generated CMake target import file for configuration "None".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "rviz_default_plugins::rviz_default_plugins" for configuration "None"
set_property(TARGET rviz_default_plugins::rviz_default_plugins APPEND PROPERTY IMPORTED_CONFIGURATIONS NONE)
set_target_properties(rviz_default_plugins::rviz_default_plugins PROPERTIES
  IMPORTED_LOCATION_NONE "${_IMPORT_PREFIX}/lib/librviz_default_plugins.so"
  IMPORTED_SONAME_NONE "librviz_default_plugins.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS rviz_default_plugins::rviz_default_plugins )
list(APPEND _IMPORT_CHECK_FILES_FOR_rviz_default_plugins::rviz_default_plugins "${_IMPORT_PREFIX}/lib/librviz_default_plugins.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
