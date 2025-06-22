#----------------------------------------------------------------
# Generated CMake target import file for configuration "None".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "rqt_image_view::rqt_image_view" for configuration "None"
set_property(TARGET rqt_image_view::rqt_image_view APPEND PROPERTY IMPORTED_CONFIGURATIONS NONE)
set_target_properties(rqt_image_view::rqt_image_view PROPERTIES
  IMPORTED_LINK_DEPENDENT_LIBRARIES_NONE "cv_bridge::cv_bridge"
  IMPORTED_LOCATION_NONE "${_IMPORT_PREFIX}/lib/rqt_image_view/librqt_image_view.so"
  IMPORTED_SONAME_NONE "librqt_image_view.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS rqt_image_view::rqt_image_view )
list(APPEND _IMPORT_CHECK_FILES_FOR_rqt_image_view::rqt_image_view "${_IMPORT_PREFIX}/lib/rqt_image_view/librqt_image_view.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
