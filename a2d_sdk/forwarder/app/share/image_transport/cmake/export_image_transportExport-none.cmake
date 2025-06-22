#----------------------------------------------------------------
# Generated CMake target import file for configuration "None".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "image_transport::image_transport" for configuration "None"
set_property(TARGET image_transport::image_transport APPEND PROPERTY IMPORTED_CONFIGURATIONS NONE)
set_target_properties(image_transport::image_transport PROPERTIES
  IMPORTED_LOCATION_NONE "${_IMPORT_PREFIX}/lib/x86_64-linux-gnu/libimage_transport.so"
  IMPORTED_SONAME_NONE "libimage_transport.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS image_transport::image_transport )
list(APPEND _IMPORT_CHECK_FILES_FOR_image_transport::image_transport "${_IMPORT_PREFIX}/lib/x86_64-linux-gnu/libimage_transport.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
