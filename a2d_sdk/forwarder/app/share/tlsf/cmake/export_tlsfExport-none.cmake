#----------------------------------------------------------------
# Generated CMake target import file for configuration "None".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "tlsf::tlsf" for configuration "None"
set_property(TARGET tlsf::tlsf APPEND PROPERTY IMPORTED_CONFIGURATIONS NONE)
set_target_properties(tlsf::tlsf PROPERTIES
  IMPORTED_LINK_INTERFACE_LANGUAGES_NONE "C"
  IMPORTED_LOCATION_NONE "${_IMPORT_PREFIX}/lib/libtlsf.a"
  )

list(APPEND _IMPORT_CHECK_TARGETS tlsf::tlsf )
list(APPEND _IMPORT_CHECK_FILES_FOR_tlsf::tlsf "${_IMPORT_PREFIX}/lib/libtlsf.a" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
