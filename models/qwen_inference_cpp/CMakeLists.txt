cmake_minimum_required(VERSION 3.18)
project(QwenInference LANGUAGES CXX CUDA)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Optimization flags for AMD Ryzen 7 7700
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -march=native -mtune=native -DNDEBUG")

# Find required packages
find_package(Torch REQUIRED)
find_package(PythonLibs REQUIRED)
find_package(pybind11 REQUIRED)

# CUDA setup for RTX 3060
enable_language(CUDA)
find_package(CUDA REQUIRED)
set(CMAKE_CUDA_STANDARD 17)
set(CMAKE_CUDA_FLAGS "${CMAKE_CUDA_FLAGS} -arch=sm_86") # RTX 3060 architecture

# Include directories
include_directories(${PYTHON_INCLUDE_DIRS})
include_directories(${TORCH_INCLUDE_DIRS})

# Source files
set(SOURCES
    src/qwen_inference.cpp
    src/memory_manager.cpp
    src/tensor_utils.cpp
    src/python_bindings.cpp
)

# Create the library
pybind11_add_module(qwen_inference_cpp ${SOURCES})

# Link libraries
target_link_libraries(qwen_inference_cpp PRIVATE ${TORCH_LIBRARIES})
target_link_libraries(qwen_inference_cpp PRIVATE ${CUDA_LIBRARIES})

# Compiler-specific options
target_compile_definitions(qwen_inference_cpp PRIVATE VERSION_INFO=${EXAMPLE_VERSION_INFO})

# Enable OpenMP for parallel processing
find_package(OpenMP)
if(OpenMP_CXX_FOUND)
    target_link_libraries(qwen_inference_cpp PRIVATE OpenMP::OpenMP_CXX)
endif()