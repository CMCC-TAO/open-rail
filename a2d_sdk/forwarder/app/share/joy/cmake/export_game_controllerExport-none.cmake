#----------------------------------------------------------------
# Generated CMake target import file for configuration "None".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "joy::game_controller" for configuration "None"
set_property(TARGET joy::game_controller APPEND PROPERTY IMPORTED_CONFIGURATIONS NONE)
set_target_properties(joy::game_controller PROPERTIES
  IMPORTED_LOCATION_NONE "${_IMPORT_PREFIX}/lib/libgame_controller.so"
  IMPORTED_SONAME_NONE "libgame_controller.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS joy::game_controller )
list(APPEND _IMPORT_CHECK_FILES_FOR_joy::game_controller "${_IMPORT_PREFIX}/lib/libgame_controller.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
