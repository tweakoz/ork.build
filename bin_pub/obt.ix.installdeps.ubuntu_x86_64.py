#!/usr/bin/env python3

import os, distro

UBUNTU_VERSION = int(float(distro.version())*100.0)

print(UBUNTU_VERSION)
os.system("sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 1")

deplist = []

if UBUNTU_VERSION >= 2310:
  deplist =  ["clang-17","g++-11"]
elif UBUNTU_VERSION <= 2004:
  deplist =  ["gcc-8","g++-8","python-dev"] # not avail in ub22
else:
  deplist += ["clang-12"]

deplist += ["libboost-dev","clang","clang-format"]
if UBUNTU_VERSION < 2604:  # dropped from the 26.04 archive (clang-17/g++-11/12 cover it)
  deplist += ["gcc-9","g++-9","gcc-10","g++-10"]
deplist += ["g++-12","gfortran"] # https://askubuntu.com/questions/1441844/todays-ubuntu-22-04-updates-seem-to-break-clang-compiler
deplist += ["libboost-filesystem-dev","libboost-system-dev","libboost-thread-dev"]
deplist += ["libboost-program-options-dev","libftdi-dev", "libfmt-dev"]
deplist += ["libglfw3-dev","libflac++-dev","scons","git"]
deplist += ["rapidjson-dev","graphviz","doxygen","libtiff-dev"]
deplist += ["portaudio19-dev", "pybind11-dev"]
deplist += ["libpng-dev"]
deplist += ["iverilog"]
deplist += ["patchelf"]  # pytorch.py: cherrypick_torch_assets uses patchelf
                         # to rewrite SONAME on the renamed libobt.torch.*
                         # dylibs (Linux equivalent of install_name_tool).
deplist += ["libopenblas-dev"]
deplist += ["librtmidi-dev"]
deplist += ["texinfo","xmlto"]
deplist += ["libgtkmm-3.0-dev"]
deplist += ["libfltk1.3-dev","freeglut3-dev"]
deplist += ["libfontconfig1-dev"]
deplist += ["libfreetype6-dev"]
deplist += ["libx11-dev"]
deplist += ["libxext-dev"]
deplist += ["libxfixes-dev"]
deplist += ["libxi-dev"]
deplist += ["libxrender-dev"]
deplist += ["libx11-xcb-dev"]
deplist += ["libavformat-dev"]
deplist += ["libavcodec-dev"]
deplist += ["libswscale-dev"]
deplist += ["libssl-dev"]
deplist += ["wget","git","git-lfs", "vim","cmake","python3-pip", "nasm"]
deplist += ["m4","bison","flex"]
deplist += ["libcurl4-openssl-dev","libusb-1.0-0-dev", "libbz2-dev"]
deplist += ["libreadline-dev"]
deplist += ["libsqlite3-dev"]
deplist += ["openctm-tools"] # ctmviewer
deplist += ["openscad"] # for trimesh
deplist += ["libclang-dev"]
deplist += ["libgmp-dev","libmpfr-dev","texinfo","libmpc-dev"]
deplist += ["libx11-dev"]
deplist += ["libx11-xcb-dev"]
deplist += ["libxext-dev"]
deplist += ["libxfixes-dev"]
deplist += ["libxi-dev"]
deplist += ["libxrender-dev"]
deplist += ["libxcb1-dev"]
deplist += ["libxcb-glx0-dev"]
deplist += ["libxcb-keysyms1-dev"]
deplist += ["libxcb-image0-dev"]
deplist += ["libxcb-shm0-dev"]
deplist += ["libxcb-icccm4-dev"]
deplist += ["libxcb-sync-dev"]
deplist += ["libxcb-xfixes0-dev"]
deplist += ["libxcb-shape0-dev"]
deplist += ["libxcb-randr0-dev"]
deplist += ["libxcb-render-util0-dev"]
deplist += ["libxcb-xinerama0-dev"]
deplist += ["libxkbcommon-dev"]
deplist += ["libxkbcommon-x11-dev"]
deplist += ["libxcb-xkb-dev"]
deplist += ["libxcb-cursor-dev"]
deplist += ["libxcb-util-dev"]
deplist += ["libmad0-dev","libsdl2-dev","libassimp-dev"]
deplist += ["device-tree-compiler"]
deplist += ["imagemagick","curl","tk-dev"]
deplist += ["libgeos-dev","libpng-dev","libspatialindex-dev"]
deplist += ["qt5ct","python3-gdal","python3-pyqt5","python3-pyqt5.qtopengl"]
if UBUNTU_VERSION < 2604:
  deplist += ["qt5-style-plugins"]  # dropped from the 26.04 archive
deplist += ["python3-simplejson","python3-tk"]

deplist += ["libdrm-dev","libaudiofile-dev","libsndfile1-dev"]
deplist += ["libglew-dev"]
deplist += ["debhelper-compat","findutils","git","libasound2-dev","libavcodec-dev","libavfilter-dev","libavformat-dev"]
deplist += ["libdbus-1-dev","libbluetooth-dev","libglib2.0-dev","libgstreamer1.0-dev","libgstreamer-plugins-base1.0-dev"]
deplist += ["libsbc-dev","libsdl2-dev","libudev-dev","libva-dev","libv4l-dev","libx11-dev","meson","ninja-build"]
deplist += ["pkg-config","python3-docutils","systemd","mesa-utils","xvfb"]
deplist += ["meson","ninja-build","libserialport-dev", "libxxhash-dev"]
deplist += ["libpipewire-0.3-dev", "pipewire", "gstreamer1.0-libav"]
deplist += ["astap","libnotcurses++-dev","libsodium-dev"]
if UBUNTU_VERSION < 2604:
  deplist += ["libtar-dev"]  # dropped from the 26.04 archive; vendor if a dep ever needs it
deplist += ["vulkan-tools","vulkan-validationlayers"]
deplist += ["libffmpeg-nvenc-dev"]
deplist += ["libshaderc-dev"]
deplist += ["libinput-dev"]
deplist += ["mold"]

merged = " ".join(deplist)
os.system("sudo apt -y install %s" % merged)

# PEP-668 (externally-managed system python, 23.04+): plain pip3 refuses; fall back.
if os.system("pip3 install os_release") != 0:
  os.system("pip3 install --break-system-packages os_release")

###############################################################################
# CUDA toolkit
#
# Old: Ubuntu's distro-packaged `nvidia-cuda-toolkit` ships CUDA 12.0 (a
# wrapper at /usr/bin/nvcc execing /usr/lib/nvidia-cuda-toolkit/bin/nvcc).
# pytorch 2.12 wants CUDA >= 12.1 and the 12.0 nvcc + 12.6 headers mix
# blows up with `__half → unsigned short` conversion errors. Remove it.
# `nvidia-profiler` and `libthrust-dev` are reverse-deps that depend on
# the old toolkit; cuda-toolkit-12-6 already supplies nsight + thrust.
#
# New: NVIDIA's apt repo. Adds /usr/local/cuda-12.6/. pytorch.py picks it
# up automatically via the CUDA_HOME probe in _build_env().
###############################################################################
# CUDA only makes sense on NVIDIA hardware (h9ixub26, an AMD box, taught us this) -
# and only where NVIDIA actually publishes a repo for this ubuntu release.
def _has_nvidia_gpu():
  return os.system("lspci 2>/dev/null | grep -qi 'nvidia'") == 0

if UBUNTU_VERSION >= 2404 and _has_nvidia_gpu():
  os.system("sudo apt -y remove nvidia-cuda-toolkit nvidia-profiler libthrust-dev")

  # per-release repo path; if NVIDIA has not published this release's repo yet the
  # keyring download fails LOUDLY below (curl -f) rather than half-configuring apt.
  _CUDA_DISTRO = "ubuntu%d" % ((UBUNTU_VERSION // 100) * 100 + (UBUNTU_VERSION % 100))
  KEYRING_URL = "https://developer.download.nvidia.com/compute/cuda/repos/%s/x86_64/cuda-keyring_1.1-1_all.deb" % _CUDA_DISTRO
  KEYRING_DEB = "/tmp/cuda-keyring_1.1-1_all.deb"
  os.system("curl -fsSL -o %s %s" % (KEYRING_DEB, KEYRING_URL))
  os.system("sudo dpkg -i %s" % KEYRING_DEB)
  os.system("sudo apt update")
  os.system("sudo apt -y install cuda-toolkit-12-8")
elif UBUNTU_VERSION >= 2404:
  print("[installdeps] no NVIDIA GPU detected - skipping the CUDA toolkit section")
