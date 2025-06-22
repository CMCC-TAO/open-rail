#----------------------------------------------------------------
# Generated CMake target import file for configuration "None".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "rosidl_typesupport_cpp::rosidl_typesupport_cpp" for configuration "None"
set_property(TARGET rosidl_typesupport_cpp::rosidl_typesupport_cpp APPEND PROPERTY IMPORTED_CONFIGURATIONS NONE)
set_target_properties(rosidl_typesupport_cpp::rosidl_typesupport_cpp PROPERTIES
  IMPORTED_LINK_DEPENDENT_LIBRARIES_NONE "rcpputils::rcpputils;rcutils::rcutils"
  IMPORTED_LOCATION_NONE "${_IMPORT_PREFIX}/lib/librosidl_typesupport_cpp.so"
  IMPORTED_SONAME_NONE "librosidl_typesupport_cpp.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS rosidl_typesupport_cpp::rosidl_typesupport_cpp )
list(APPEND _IMPORT_CHECK_FILES_FOR_rosidl_typesupport_cpp::rosidl_typesupport_cpp "${_IMPORT_PREFIX}/lib/librosidl_typesupport_cpp.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
