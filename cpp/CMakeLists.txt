cmake_minimum_required(VERSION 3.20)
project(vehicle_fault_monitor LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(vehicle_fault_monitor STATIC
    src/fault_monitor.cpp
)
target_include_directories(vehicle_fault_monitor PUBLIC include)
target_compile_options(vehicle_fault_monitor PRIVATE -Wall -Wextra -Wpedantic)

add_executable(fault_monitor_cli src/fault_monitor_cli.cpp)
target_link_libraries(fault_monitor_cli PRIVATE vehicle_fault_monitor)

include(CTest)
if(BUILD_TESTING)
    add_executable(test_fault_monitor tests/test_fault_monitor.cpp)
    target_link_libraries(test_fault_monitor PRIVATE vehicle_fault_monitor)
    add_test(NAME fault_monitor_cpp COMMAND test_fault_monitor)
endif()
