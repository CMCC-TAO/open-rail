# Copyright 2014-2016 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# generated from rmw_implementation/rmw_implementation-extras.cmake.in

find_package(rmw_implementation_cmake REQUIRED)

get_default_rmw_implementation(requested_rmw_implementation)
set(requested_rmw_implementation_from "get_default_rmw_implementation")

if(OFF)
  message(STATUS "Using RMW implementation 'rmw_fastrtps_cpp'")
  if(NOT requested_rmw_implementation STREQUAL "rmw_fastrtps_cpp")
    message(FATAL_ERROR
      "The RMW implementation has been specified as "
      "'${requested_rmw_implementation}' via "
      "${requested_rmw_implementation_from}, but rmw_implementation was built "
      "only with support for 'rmw_fastrtps_cpp'.")
  endif()
  find_package("rmw_fastrtps_cpp" REQUIRED)

  # Create a target rmw_implementation::rmw_implementation that depends on the real implementation
  add_library(rmw_implementation::rmw_implementation INTERFACE IMPORTED)

  if(DEFINED rmw_fastrtps_cpp_TARGETS)
    # First preference: depend on all targets exported by the package
    target_link_libraries(rmw_implementation::rmw_implementation INTERFACE
      ${rmw_fastrtps_cpp_TARGETS})
  elseif(TARGET rmw_fastrtps_cpp::rmw_fastrtps_cpp)
    # Next preference: depend on a target with the package's name
    target_link_libraries(rmw_implementation::rmw_implementation INTERFACE
      rmw_fastrtps_cpp::rmw_fastrtps_cpp)
  else()
    # Last resort: assume old-style CMake variables are set
    target_compile_definitions(rmw_implementation::rmw_implementation INTERFACE
      ${rmw_fastrtps_cpp_DEFINITIONS})
    target_include_directories(rmw_implementation::rmw_implementation INTERFACE
      ${rmw_fastrtps_cpp_INCLUDE_DIRS})
    target_link_libraries(rmw_implementation::rmw_implementation INTERFACE
      ${rmw_fastrtps_cpp_LIBRARIES})
  endif()

  list(APPEND rmw_implementation_TARGETS
    rmw_implementation::rmw_implementation)
else()
  get_available_rmw_implementations(available_rmw_implementations)

  if(NOT requested_rmw_implementation IN_LIST available_rmw_implementations)
    message(FATAL_ERROR
      "The RMW implementation has been specified as "
      "'${requested_rmw_implementation}' via "
      "${requested_rmw_implementation_from}, but it is not available at this "
      "time.\n\nCurrently available middlewares:\n"
      "'${available_rmw_implementations}'")
  endif()
  message(STATUS "Using RMW implementation '${requested_rmw_implementation}' as default")

  # no need to find_package rmw_implementation
  # since this code is already part of a find_package call of that package
endif()
