# Open Image Denoise

`obt.dep.build.py oidn` builds OIDN 2.5.1 from
`git@github.com:tweakoz/oidn.git`, tag `v2.5.1` (commit
`6602ee2ca38a1a2a02135beed8f6e68eed630180`). The fork is the source of truth.
Git SSH access and Git LFS are required. The weights submodule uses the absolute
upstream URL because its relative URL would resolve to the fork owner's account.
Only weights and requested GPU backend submodules are fetched.

The default build includes CPU support on Linux x86-64 and macOS, plus Metal on
Apple Silicon. It uses staged TBB and ISPC; Linux's ISPC provider is updated to
1.31.0, and an older staged ISPC triggers its upgrade. Intel macOS uses the
existing Homebrew ISPC provider and needs ISPC >=1.30.

Libraries install in `$OBT_STAGE/lib`, headers in `$OBT_STAGE/include`, and
`oidnDenoise`, `oidnBenchmark`, and `oidnTest` in `$OBT_STAGE/bin`.
CMake consumers use `find_package(OpenImageDenoise 2.5 CONFIG REQUIRED)` and
link `OpenImageDenoise`. Runtime device modules are versioned shared libraries;
installing only the public front-end library is insufficient.

## GPU options

```sh
# NVIDIA on Linux: requires a system CUDA Toolkit >=12.8.
OBT_OIDN_CUDA=1 CUDAToolkit_ROOT=/usr/local/cuda obt.dep.build.py oidn

# AMD on Linux: requires a system ROCm/HIP >=6.4.2.
OBT_OIDN_HIP=1 ROCM_PATH=/opt/rocm obt.dep.build.py oidn

# Both may be enabled in one Linux build. CPU support remains enabled.
OBT_OIDN_CUDA=1 OBT_OIDN_HIP=1 obt.dep.build.py oidn

# Explicit CPU-only Apple Silicon build if desired.
OBT_OIDN_METAL=0 obt.dep.build.py oidn --force
```

Backend flags accept `0/1`, `off/on`, or `false/true`. CUDA uses the driver API.
The depper does not install system GPU drivers or CUDA/ROCm toolkits. Upstream
CMake checks toolkits and selects its separate CUDA/HIP compilation pipeline.
The selected CUDA toolkit must support the host C++ compiler. HIP builds can
use substantial memory because upstream compiles several GPU architectures.
When changing an existing build configuration, use `--force` to reconfigure.

Metal requires the Xcode Metal tools (`metal` and `metallib`) and a macOS SDK
>=14; the GPU backend runs on macOS >=13. If Xcode reports a missing component:

```sh
xcodebuild -downloadComponent MetalToolchain
```

OIDN is Apache 2.0 licensed. Its installed documentation includes license and
third-party notices. This depper installs the library and utilities; renderer
integration is separate. CPU/Metal/CUDA/HIP performance and image quality must
be measured on the actual target hardware.
