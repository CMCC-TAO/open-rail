#----------------------------------------------------------------
# Generated CMake target import file for configuration "None".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "message_filters::message_filters" for configuration "None"
set_property(TARGET message_filters::message_filters APPEND PROPERTY IMPORTED_CONFIGURATIONS NONE)
set_target_properties(message_filters::message_filters PROPERTIES
  IMPORTED_LOCATION_NONE "${_IMPORT_PREFIX}/lib/libmessage_filters.so"
  IMPORTED_SONAME_NONE "libmessage_filters.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS message_filters::message_filters )
list(APPEND _IMPORT_CHECK_FILES_FOR_message_filters::message_filters "${_IMPORT_PREFIX}/lib/libmessage_filters.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
