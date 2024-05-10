set(IOS_SDK_PATH $ENV{IOS_SDK_DIR})
set(CMAKE_SYSTEM_NAME iOS)

# Specify the architectures to build for (e.g., arm64 for actual devices)
set(CMAKE_OSX_ARCHITECTURES arm64)

# Specify the minimum iOS deployment target
set(CMAKE_OSX_DEPLOYMENT_TARGET $ENV{IOS_SDK_VER})

# Specify the path to the compiler
set(CMAKE_C_COMPILER $ENV{IOS_CLANG_PATH})
set(CMAKE_CXX_COMPILER $ENV{IOS_CLANGPP_PATH})
set(CMAKE_INSTALL_PREFIX $ENV{OBT_SUBSPACE_BUILD_DIR})
