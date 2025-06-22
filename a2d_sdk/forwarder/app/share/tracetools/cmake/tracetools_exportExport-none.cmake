#----------------------------------------------------------------
# Generated CMake target import file for configuration "None".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "tracetools::tracetools" for configuration "None"
set_property(TARGET tracetools::tracetools APPEND PROPERTY IMPORTED_CONFIGURATIONS NONE)
set_target_properties(tracetools::tracetools PROPERTIES
  IMPORTED_LOCATION_NONE "${_IMPORT_PREFIX}/lib/libtracetools.so"
  IMPORTED_SONAME_NONE "libtracetools.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS tracetools::tracetools )
list(APPEND _IMPORT_CHECK_FILES_FOR_tracetools::tracetools "${_IMPORT_PREFIX}/lib/libtracetools.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
