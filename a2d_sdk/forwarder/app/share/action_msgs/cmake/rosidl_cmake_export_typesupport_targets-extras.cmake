# generated from
# rosidl_cmake/cmake/template/rosidl_cmake_export_typesupport_targets.cmake.in

set(_exported_typesupport_targets
  "__rosidl_generator_c:action_msgs__rosidl_generator_c;__rosidl_typesupport_fastrtps_c:action_msgs__rosidl_typesupport_fastrtps_c;__rosidl_generator_cpp:action_msgs__rosidl_generator_cpp;__rosidl_typesupport_fastrtps_cpp:action_msgs__rosidl_typesupport_fastrtps_cpp;__rosidl_typesupport_introspection_c:action_msgs__rosidl_typesupport_introspection_c;__rosidl_typesupport_c:action_msgs__rosidl_typesupport_c;__rosidl_typesupport_introspection_cpp:action_msgs__rosidl_typesupport_introspection_cpp;__rosidl_typesupport_cpp:action_msgs__rosidl_typesupport_cpp;__rosidl_generator_py:action_msgs__rosidl_generator_py")

# populate action_msgs_TARGETS_<suffix>
if(NOT _exported_typesupport_targets STREQUAL "")
  # loop over typesupport targets
  foreach(_tuple ${_exported_typesupport_targets})
    string(REPLACE ":" ";" _tuple "${_tuple}")
    list(GET _tuple 0 _suffix)
    list(GET _tuple 1 _target)

    set(_target "action_msgs::${_target}")
    if(NOT TARGET "${_target}")
      # the exported target must exist
      message(WARNING "Package 'action_msgs' exports the typesupport target '${_target}' which doesn't exist")
    else()
      list(APPEND action_msgs_TARGETS${_suffix} "${_target}")
    endif()
  endforeach()
endif()
