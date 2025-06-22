# generated from
# rosidl_cmake/cmake/template/rosidl_cmake_export_typesupport_targets.cmake.in

set(_exported_typesupport_targets
  "__rosidl_generator_c:visualization_msgs__rosidl_generator_c;__rosidl_typesupport_fastrtps_c:visualization_msgs__rosidl_typesupport_fastrtps_c;__rosidl_generator_cpp:visualization_msgs__rosidl_generator_cpp;__rosidl_typesupport_fastrtps_cpp:visualization_msgs__rosidl_typesupport_fastrtps_cpp;__rosidl_typesupport_introspection_c:visualization_msgs__rosidl_typesupport_introspection_c;__rosidl_typesupport_c:visualization_msgs__rosidl_typesupport_c;__rosidl_typesupport_introspection_cpp:visualization_msgs__rosidl_typesupport_introspection_cpp;__rosidl_typesupport_cpp:visualization_msgs__rosidl_typesupport_cpp;__rosidl_generator_py:visualization_msgs__rosidl_generator_py")

# populate visualization_msgs_TARGETS_<suffix>
if(NOT _exported_typesupport_targets STREQUAL "")
  # loop over typesupport targets
  foreach(_tuple ${_exported_typesupport_targets})
    string(REPLACE ":" ";" _tuple "${_tuple}")
    list(GET _tuple 0 _suffix)
    list(GET _tuple 1 _target)

    set(_target "visualization_msgs::${_target}")
    if(NOT TARGET "${_target}")
      # the exported target must exist
      message(WARNING "Package 'visualization_msgs' exports the typesupport target '${_target}' which doesn't exist")
    else()
      list(APPEND visualization_msgs_TARGETS${_suffix} "${_target}")
    endif()
  endforeach()
endif()
