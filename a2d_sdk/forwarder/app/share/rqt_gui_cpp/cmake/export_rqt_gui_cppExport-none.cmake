#----------------------------------------------------------------
# Generated CMake target import file for configuration "None".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "rqt_gui_cpp::rqt_gui_cpp" for configuration "None"
set_property(TARGET rqt_gui_cpp::rqt_gui_cpp APPEND PROPERTY IMPORTED_CONFIGURATIONS NONE)
set_target_properties(rqt_gui_cpp::rqt_gui_cpp PROPERTIES
  IMPORTED_LOCATION_NONE "${_IMPORT_PREFIX}/lib/librqt_gui_cpp.so"
  IMPORTED_SONAME_NONE "librqt_gui_cpp.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS rqt_gui_cpp::rqt_gui_cpp )
list(APPEND _IMPORT_CHECK_FILES_FOR_rqt_gui_cpp::rqt_gui_cpp "${_IMPORT_PREFIX}/lib/librqt_gui_cpp.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
