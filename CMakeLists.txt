cmake_minimum_required(VERSION 3.15)
project(PhysXBlenderSmoke VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find OpenVDB
find_package(OpenVDB REQUIRED)

# Include directories for NVIDIA Flow
set(NVFLOW_INCLUDE_DIR ${CMAKE_SOURCE_DIR}/vendor/PhysX/flow/include)
set(NVFLOW_LIB_DIR ${CMAKE_SOURCE_DIR}/vendor/PhysX/flow/_build/linux-x86_64/release)

# Create the executable
add_executable(flow_to_vdb_minimal
    src/main.cpp
    src/FlowEngine.cpp
)

target_include_directories(flow_to_vdb_minimal PRIVATE
    ${NVFLOW_INCLUDE_DIR}
    ${NVFLOW_INCLUDE_DIR}/nvflow
    ${NVFLOW_INCLUDE_DIR}/nvflow/shaders
    ${NVFLOW_INCLUDE_DIR}/nvflowext/shaders
    src
)

# Link directories for NVIDIA Flow
target_link_directories(flow_to_vdb_minimal PRIVATE
    ${NVFLOW_LIB_DIR}
)

# Link libraries
target_link_libraries(flow_to_vdb_minimal PRIVATE
    OpenVDB::openvdb
    nvflow
    nvflowext
)

# RPATH so it can find the .so files at runtime
set_target_properties(flow_to_vdb_minimal PROPERTIES
    INSTALL_RPATH "${NVFLOW_LIB_DIR}"
    BUILD_WITH_INSTALL_RPATH TRUE
)
