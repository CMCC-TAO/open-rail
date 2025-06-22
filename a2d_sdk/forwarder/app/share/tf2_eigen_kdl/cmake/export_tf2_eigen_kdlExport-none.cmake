#----------------------------------------------------------------
# Generated CMake target import file for configuration "None".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "tf2_eigen_kdl::tf2_eigen_kdl" for configuration "None"
set_property(TARGET tf2_eigen_kdl::tf2_eigen_kdl APPEND PROPERTY IMPORTED_CONFIGURATIONS NONE)
set_target_properties(tf2_eigen_kdl::tf2_eigen_kdl PROPERTIES
  IMPORTED_LOCATION_NONE "${_IMPORT_PREFIX}/lib/libtf2_eigen_kdl.so"
  IMPORTED_SONAME_NONE "libtf2_eigen_kdl.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS tf2_eigen_kdl::tf2_eigen_kdl )
list(APPEND _IMPORT_CHECK_FILES_FOR_tf2_eigen_kdl::tf2_eigen_kdl "${_IMPORT_PREFIX}/lib/libtf2_eigen_kdl.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
