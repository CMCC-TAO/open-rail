#----------------------------------------------------------------
# Generated CMake target import file for configuration "None".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "class_loader::class_loader" for configuration "None"
set_property(TARGET class_loader::class_loader APPEND PROPERTY IMPORTED_CONFIGURATIONS NONE)
set_target_properties(class_loader::class_loader PROPERTIES
  IMPORTED_LOCATION_NONE "${_IMPORT_PREFIX}/lib/libclass_loader.so"
  IMPORTED_SONAME_NONE "libclass_loader.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS class_loader::class_loader )
list(APPEND _IMPORT_CHECK_FILES_FOR_class_loader::class_loader "${_IMPORT_PREFIX}/lib/libclass_loader.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
