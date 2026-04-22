cmake_minimum_required(VERSION 3.15)
project(PhysXBlenderSmoke VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# AddressSanitizer for memory error detection
option(ENABLE_ASAN "Enable AddressSanitizer for memory debugging" OFF)
if(ENABLE_ASAN)
    message(STATUS "AddressSanitizer enabled")
    add_compile_options(-fsanitize=address -fno-omit-frame-pointer -g)
    add_link_options(-fsanitize=address)
endif()

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
# Use $ORIGIN/libs for installed binaries and include the build-time lib path
set_target_properties(flow_to_nvdb_minimal PROPERTIES
    BUILD_RPATH "${NVFLOW_LIB_DIR}"
    INSTALL_RPATH "\$ORIGIN/libs;${NVFLOW_LIB_DIR}"
)
