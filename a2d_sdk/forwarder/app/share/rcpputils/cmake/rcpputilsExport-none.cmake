#----------------------------------------------------------------
# Generated CMake target import file for configuration "None".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "rcpputils::rcpputils" for configuration "None"
set_property(TARGET rcpputils::rcpputils APPEND PROPERTY IMPORTED_CONFIGURATIONS NONE)
set_target_properties(rcpputils::rcpputils PROPERTIES
  IMPORTED_LOCATION_NONE "${_IMPORT_PREFIX}/lib/librcpputils.so"
  IMPORTED_SONAME_NONE "librcpputils.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS rcpputils::rcpputils )
list(APPEND _IMPORT_CHECK_FILES_FOR_rcpputils::rcpputils "${_IMPORT_PREFIX}/lib/librcpputils.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
