#----------------------------------------------------------------
# Generated CMake target import file for configuration "None".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "rosidl_typesupport_c::rosidl_typesupport_c" for configuration "None"
set_property(TARGET rosidl_typesupport_c::rosidl_typesupport_c APPEND PROPERTY IMPORTED_CONFIGURATIONS NONE)
set_target_properties(rosidl_typesupport_c::rosidl_typesupport_c PROPERTIES
  IMPORTED_LINK_DEPENDENT_LIBRARIES_NONE "rcpputils::rcpputils;rcutils::rcutils"
  IMPORTED_LOCATION_NONE "${_IMPORT_PREFIX}/lib/librosidl_typesupport_c.so"
  IMPORTED_SONAME_NONE "librosidl_typesupport_c.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS rosidl_typesupport_c::rosidl_typesupport_c )
list(APPEND _IMPORT_CHECK_FILES_FOR_rosidl_typesupport_c::rosidl_typesupport_c "${_IMPORT_PREFIX}/lib/librosidl_typesupport_c.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
