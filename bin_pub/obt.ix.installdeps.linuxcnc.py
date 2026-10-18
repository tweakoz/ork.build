#!/usr/bin/env python3
###############################################################################
# obt.ix.installdeps.linuxcnc.py
#
# Host build prerequisites for a LinuxCNC box: Debian 12 "bookworm", x86_64,
# LinuxCNC 2.9-uspace. This is the FULL engine-build set (not a run-only
# minimal like obt.ix.installdeps.ub26.minimal.py).
#
# 2026-08-18 rebase:
#   The previous revision was a stale fork of obt.ix.installdeps.ubuntu_x86_64.py
#   and had drifted 47 packages behind it. Three defects, all fixed here:
#
#   1. `deplist = ["clang-11"]` used `=`, not `+=` — it CLOBBERED the line above
#      it, so the gcc-8/g++-8/python-dev entries had never been installed by any
#      run of this script. clang-11 itself is bullseye-era and has no bookworm
#      candidate, so apt aborted the whole transaction before installing
#      anything. That abort is why the box had no dep set at all.
#   2. libffmpeg-nvenc-dev was missing. modules/dep/ffmpeg.py passes
#      --enable-nvenc on every Linux x86_64 host, and ffmpeg's configure hard
#      -fails ("nvenc requested, but not all dependencies are satisfied:
#      ffnvcodec") without those headers. The failed ffmpeg build aborted the
#      dep phase, so openblas never got staged either — which surfaced later as
#      the misleading "Could NOT find ObtOpenBlas" from cmake (FindObtOpenBlas
#      searches $OBT_STAGE only, NO_DEFAULT_PATH; the system libopenblas-dev is
#      not a substitute). The package is headers only — no driver, no GPU
#      required — so it is unconditional, matching ubuntu_x86_64.
#   3. mold, gfortran, ninja-build, meson, pkg-config and patchelf were absent
#      even though ork.build links with -fuse-ld=mold and openblas needs a
#      Fortran compiler for LAPACK.
#
#   Every package below was verified present in the bookworm archive on the
#   target box (apt-cache policy, 2026-08-18) per the no-guessed-values rule. The
#   ubuntu_x86_64 entries with NO bookworm candidate are deliberately dropped
#   and named in DROPPED_ON_BOOKWORM at the bottom, so the next person diffing
#   the two scripts sees why rather than re-adding them.
###############################################################################

import os, sys, distro

DISTRO_ID = distro.id()            # "debian" on a LinuxCNC 2.9-uspace box
DISTRO_CODENAME = distro.codename() # "bookworm"

print("[installdeps.linuxcnc] distro=%s version=%s codename=%s" %
      (DISTRO_ID, distro.version(), DISTRO_CODENAME))

# The package set below is bookworm-verified. Refuse to run it blind on a
# release it was never checked against - a wrong name aborts the ENTIRE apt
# transaction (defect 1 above), so a loud stop beats a half-installed box.
if DISTRO_CODENAME != "bookworm":
  print("[installdeps.linuxcnc] this script is verified for Debian 12 "
        "'bookworm' only; refusing to run on '%s'." % DISTRO_CODENAME)
  print("[installdeps.linuxcnc] re-verify the deplist against that release "
        "(apt-cache policy) and widen this gate before using it.")
  sys.exit(1)

os.system("sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 1")

deplist = []

###############################################################################
# toolchain
#
# clang-16 is REQUIRED, not optional: modules/dep/clang.py maps codename ->
# compiler and bookworm resolves to clang-16 / clang++-16. Plain "clang" on
# bookworm is 14 and does NOT satisfy that mapping.
###############################################################################
deplist += ["build-essential","clang","clang-16","clang-format","libclang-dev"]
deplist += ["g++-11","g++-12","gfortran"]
deplist += ["cmake","meson","ninja-build","pkg-config","scons","make"]
deplist += ["mold"]      # ork.build links with -fuse-ld=mold on linux
deplist += ["patchelf"]  # pytorch.py cherrypick_torch_assets rewrites SONAMEs
deplist += ["nasm","m4","bison","flex"]
deplist += ["python3-dev","python3-pip","python3-venv"]

###############################################################################
# boost / core libs
###############################################################################
deplist += ["libboost-dev","libboost-filesystem-dev","libboost-system-dev"]
deplist += ["libboost-thread-dev","libboost-program-options-dev"]
deplist += ["libfmt-dev","rapidjson-dev","libssl-dev","libsodium-dev"]
deplist += ["libgmp-dev","libmpfr-dev","libmpc-dev"]
deplist += ["libcurl4-openssl-dev","libusb-1.0-0-dev","libftdi-dev"]
deplist += ["libserialport-dev","libbz2-dev","libreadline-dev","libsqlite3-dev"]
deplist += ["libxxhash-dev","libtar-dev","libjemalloc-dev","libtbb-dev"]
deplist += ["libopenblas-dev"]

###############################################################################
# media
#
# libffmpeg-nvenc-dev = the ffnvcodec headers. Headers only; installing them
# needs no NVIDIA hardware and no driver. Required because
# modules/dep/ffmpeg.py sets --enable-nvenc on every linux/x86_64 host.
###############################################################################
deplist += ["libffmpeg-nvenc-dev"]
deplist += ["libavformat-dev","libavcodec-dev","libavfilter-dev","libswscale-dev"]
deplist += ["libva-dev","libv4l-dev"]
deplist += ["libgstreamer1.0-dev","libgstreamer-plugins-base1.0-dev","gstreamer1.0-libav"]
deplist += ["libflac++-dev","libmad0-dev","libsndfile1-dev","libaudiofile-dev"]
deplist += ["portaudio19-dev","librtmidi-dev","libasound2-dev"]
deplist += ["libpipewire-0.3-dev","pipewire","libsbc-dev"]
deplist += ["libpng-dev","libtiff-dev","imagemagick"]

###############################################################################
# graphics / windowing
###############################################################################
deplist += ["libglfw3-dev","libglew-dev","freeglut3-dev","libdrm-dev"]
deplist += ["vulkan-tools","vulkan-validationlayers","libshaderc-dev"]
deplist += ["mesa-utils","xvfb"]
deplist += ["libfontconfig1-dev","libfreetype6-dev"]
deplist += ["libx11-dev","libx11-xcb-dev","libxext-dev","libxfixes-dev"]
deplist += ["libxi-dev","libxrender-dev"]
deplist += ["libxcb1-dev","libxcb-glx0-dev","libxcb-keysyms1-dev"]
deplist += ["libxcb-image0-dev","libxcb-shm0-dev","libxcb-icccm4-dev"]
deplist += ["libxcb-sync-dev","libxcb-xfixes0-dev","libxcb-shape0-dev"]
deplist += ["libxcb-randr0-dev","libxcb-render-util0-dev","libxcb-xinerama0-dev"]
deplist += ["libxcb-cursor-dev","libxcb-xkb-dev","libxcb-util-dev"]
deplist += ["libxkbcommon-dev","libxkbcommon-x11-dev"]
deplist += ["libinput-dev","libudev-dev","libdbus-1-dev","libglib2.0-dev"]
deplist += ["libbluetooth-dev"]

###############################################################################
# assets / tools / bindings
###############################################################################
deplist += ["libassimp-dev","libsdl2-dev","libopencv-dev"]
deplist += ["libgeos-dev","libspatialindex-dev"]
deplist += ["openctm-tools"]   # ctmviewer
deplist += ["openscad"]        # for trimesh
deplist += ["pybind11-dev"]
deplist += ["libgtkmm-3.0-dev","libfltk1.3-dev","tk-dev"]
deplist += ["qt5ct","qt5-style-plugins"]
deplist += ["python3-gdal","python3-pyqt5","python3-pyqt5.qtopengl"]
deplist += ["python3-simplejson","python3-tk","python3-docutils"]
deplist += ["iverilog","device-tree-compiler","astap"]
deplist += ["graphviz","doxygen","texinfo","xmlto"]
deplist += ["debhelper","findutils","systemd"]
deplist += ["wget","curl","git","git-lfs","vim"]

###############################################################################
# in ubuntu_x86_64.py, NOT here - no bookworm candidate (verified 2026-08-18).
# Listed rather than silently omitted so a future diff of the two scripts is
# self-explaining.
#
#   clang-12, clang-17, gcc-9, g++-9, gcc-10, g++-10
#                       ubuntu-only compiler pins; bookworm ships clang-14/16
#                       and gcc-12, which cover every ork.build codename map.
#   gcc-8, g++-8, python-dev, clang-11
#                       bullseye-era and older; the dead lines that broke this
#                       script (defect 1 above).
#   debhelper-compat    a virtual package on bookworm - real `debhelper` above.
#   libnotcurses++-dev  not packaged for bookworm at any version. If a dep ever
#                       hard-requires notcurses here it must be vendored.
###############################################################################

merged = " ".join(deplist)
os.system("sudo apt update")
os.system("sudo apt -y install %s" % merged)

# PEP-668: bookworm's system python3.11 is externally-managed
# (/usr/lib/python3.11/EXTERNALLY-MANAGED), so plain pip3 refuses. Fall back.
if os.system("pip3 install os_release") != 0:
  os.system("pip3 install --break-system-packages os_release")

###############################################################################
# No CUDA section (cf. ubuntu_x86_64.py): a LinuxCNC box is not NVIDIA
# hardware by definition - the box is an Intel Xeon E3-1200 v3 iGPU
# (lspci, 2026-08-18). Add the probe from ubuntu_x86_64.py if that changes.
###############################################################################
