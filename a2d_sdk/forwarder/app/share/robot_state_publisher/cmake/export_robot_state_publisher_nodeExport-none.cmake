#----------------------------------------------------------------
# Generated CMake target import file for configuration "None".
#----------------------------------------------------------------

# Commands may need to know the format version.
set(CMAKE_IMPORT_FILE_VERSION 1)

# Import target "robot_state_publisher::robot_state_publisher_node" for configuration "None"
set_property(TARGET robot_state_publisher::robot_state_publisher_node APPEND PROPERTY IMPORTED_CONFIGURATIONS NONE)
set_target_properties(robot_state_publisher::robot_state_publisher_node PROPERTIES
  IMPORTED_LOCATION_NONE "${_IMPORT_PREFIX}/lib/librobot_state_publisher_node.so"
  IMPORTED_SONAME_NONE "librobot_state_publisher_node.so"
  )

list(APPEND _IMPORT_CHECK_TARGETS robot_state_publisher::robot_state_publisher_node )
list(APPEND _IMPORT_CHECK_FILES_FOR_robot_state_publisher::robot_state_publisher_node "${_IMPORT_PREFIX}/lib/librobot_state_publisher_node.so" )

# Commands beyond this point should not need to know the version.
set(CMAKE_IMPORT_FILE_VERSION)
