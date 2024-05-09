cmake_minimum_required(VERSION 3.28.3)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED on)

project(ios_minimal_app LANGUAGES CXX OBJCXX)
set(CMAKE_OSX_SYSROOT %s CACHE PATH "The iOS SDK sysroot")

include($ENV{OBT_SUBSPACE_DIR}/ios.toolchain.cmake)

# Find the required frameworks
find_library(UIKit UIKit REQUIRED)
find_library(Foundation Foundation REQUIRED)
find_library(CoreGraphics CoreGraphics REQUIRED)

add_executable(${PROJECT_NAME} $ENV{OBT_ROOT}/modules/subspace/ios/main.mm)

target_include_directories (${PROJECT_NAME} PRIVATE $ENV{OBT_SUBSPACE_DIR}/include)

# Link against the required frameworks
target_link_libraries(${PROJECT_NAME} PRIVATE ${UIKit} ${Foundation} ${CoreGraphics})

set_target_properties(${PROJECT_NAME} PROPERTIES
    XCODE_ATTRIBUTE_PRODUCT_BUNDLE_IDENTIFIER "com.example.minimalapp"
    XCODE_ATTRIBUTE_DEVELOPMENT_TEAM "$ENV{DEVELOPMENT_TEAM}"
    XCODE_ATTRIBUTE_CODE_SIGN_IDENTITY "iPhone Developer"
    XCODE_ATTRIBUTE_CODE_SIGN_STYLE "Automatic"
    MACOSX_BUNDLE_GUI_IDENTIFIER "com.example.minimalapp"
    MACOSX_BUNDLE_INFO_PLIST ${CMAKE_CURRENT_SOURCE_DIR}/Info.plist)

    