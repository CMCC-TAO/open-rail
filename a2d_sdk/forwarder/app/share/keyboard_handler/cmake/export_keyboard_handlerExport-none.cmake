#----------------------------------------------------------------
# Generated CMake target import file for configuration "None".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "keyboard_handler::keyboard_handler" for configuration "None"
set_property(TARGET keyboard_handler::keyboard_handler APPEND PROPERTY IMPORTED_CONFIGURATIONS NONE)
set_target_properties(keyboard_handler::keyboard_handler PROPERTIES
  IMPORTED_LOCATION_NONE "${_IMPORT_PREFIX}/lib/libkeyboard_handler.so"
  IMPORTED_SONAME_NONE "libkeyboard_handler.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS keyboard_handler::keyboard_handler )
list(APPEND _IMPORT_CHECK_FILES_FOR_keyboard_handler::keyboard_handler "${_IMPORT_PREFIX}/lib/libkeyboard_handler.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
