cmake_minimum_required(VERSION 3.15)
project(PhysXBlenderSmoke VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(NVFLOW_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/vendor/PhysX/flow/include")
set(NVFLOW_LIB_DIR "${CMAKE_CURRENT_SOURCE_DIR}/vendor/PhysX/flow/_build/linux-x86_64/release")

add_executable(flow_to_nvdb_minimal src/main.cpp src/simulation.cpp)

target_include_directories(flow_to_nvdb_minimal PRIVATE
    ${NVFLOW_INCLUDE_DIR}
    ${NVFLOW_INCLUDE_DIR}/nvflow
    ${NVFLOW_INCLUDE_DIR}/nvflow/shaders
    ${NVFLOW_INCLUDE_DIR}/nvflowext/shaders
    /usr/include
)

target_link_libraries(flow_to_nvdb_minimal PRIVATE
    openvdb
    tbb
    Imath
)

# Embed the library path directly into the executable's RPATH
set_target_properties(flow_to_nvdb_minimal PROPERTIES
    BUILD_RPATH "${NVFLOW_LIB_DIR}"
    INSTALL_RPATH "${NVFLOW_LIB_DIR}"
)
