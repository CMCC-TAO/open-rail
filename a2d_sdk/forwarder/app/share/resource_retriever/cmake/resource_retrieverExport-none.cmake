#----------------------------------------------------------------
# Generated CMake target import file for configuration "None".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "resource_retriever::resource_retriever" for configuration "None"
set_property(TARGET resource_retriever::resource_retriever APPEND PROPERTY IMPORTED_CONFIGURATIONS NONE)
set_target_properties(resource_retriever::resource_retriever PROPERTIES
  IMPORTED_LOCATION_NONE "${_IMPORT_PREFIX}/lib/libresource_retriever.so"
  IMPORTED_SONAME_NONE "libresource_retriever.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS resource_retriever::resource_retriever )
list(APPEND _IMPORT_CHECK_FILES_FOR_resource_retriever::resource_retriever "${_IMPORT_PREFIX}/lib/libresource_retriever.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
