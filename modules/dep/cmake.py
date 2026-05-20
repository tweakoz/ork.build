###############################################################################
# Orkid Build System
# Copyright 2010-2026, Michael T. Mayers
# email: michael@tweakoz.com
# Published under GPL 2.0 license
###############################################################################
# CMake — bootstrapped using its own ./bootstrap script (compiles a minimal
# cmake via just a C++ compiler, then uses that to configure the full build).
# Avoids the chicken-and-egg of needing /opt/homebrew/bin/cmake to build cmake.
###############################################################################

from obt import dep, path, host
from obt.command import Command

###############################################################################

class cmake(dep.StdProvider):
    name = "cmake"

    def __init__(self):
        super().__init__(cmake.name)
        # cmake's own ./bootstrap doesn't need pkg-config (it has its own
        # bundled detection for the libs it cares about). Removed
        # declareDep("pkgconfig") — part of the iterative pkgconfig severance.

        # HTTPS support for cmake's file(DOWNLOAD) and FetchContent — needed
        # whenever a downstream cmake invocation pulls deps via https URLs
        # (e.g. cpppeglib's test/CMakeLists.txt FetchContent_Declares
        # googletest). Path:
        #   --system-curl     : link cmake's CURL backend against the host
        #                       libcurl (macOS: /usr/lib/libcurl, Linux:
        #                       system libcurl). Both ship with TLS already
        #                       configured against the platform's CA store.
        #                       This bypasses cmake's bundled libcurl entirely,
        #                       so we never hit the "Protocol https not
        #                       supported or disabled in libcurl" error.
        #   CMAKE_USE_OPENSSL : LEFT OFF deliberately. Past experiment that
        #                       linked cmake's libcurl against the OBT openssl
        #                       caused cmake to hang in execute_process()
        #                       — likely FD_CLOEXEC missing on an openssl-
        #                       opened fd holding the child's cmsysProcess
        #                       pipe write-end open. With --system-curl we
        #                       don't link openssl into cmake at all; the
        #                       system curl already has TLS wired up against
        #                       Secure Transport (macOS) or system openssl
        #                       (Linux) by the OS vendor.

        bdir = self.source_root

        # cmake's own bootstrap script avoids needing a host cmake.
        # `--system-zlib`: cmake 3.28's bundled zlib redefines fdopen as NULL,
        # which conflicts with macOS SDK 26.4 (Tahoe)'s modern stdio.h. Using
        # the SDK's zlib avoids the conflict.
        bootstrap_cmd = Command([
            "./bootstrap",
            "--prefix=%s" % path.prefix(),
            "--parallel=%s" % host.NumCores,
            "--system-zlib",
            "--system-curl",
            "--",
            "-DCMAKE_USE_OPENSSL=OFF",          # see comment above
            "-DBUILD_TESTING=OFF",
        ], working_dir=bdir)

        make_cmd    = Command(["make", "-j", host.NumCores], working_dir=bdir)
        install_cmd = Command(["make", "install"], working_dir=bdir)

        self._builder = dep.CustomBuilder(cmake.name)
        self._builder._cleanbuildcommands = [bootstrap_cmd, make_cmd, install_cmd]
        self._builder._incrbuildcommands  = [make_cmd, install_cmd]
        self._builder._builddir = bdir

    def __str__(self):
        return "cmake (kitware-source-bootstrap)"

    @property
    def _fetcher(self):
        return dep.GithubFetcher(name=cmake.name,
                                 repospec="kitware/cmake",
                                 # 3.31.12 is the latest 3.x line as of
                                 # 2026-05. Picked over 4.x because 4.x
                                 # refuses cmake_minimum_required<3.5
                                 # (breaks jpegturbo 2.1.2, sox-14.4.2,
                                 # other old-school projects). 3.31.x
                                 # carries ~2 years of cmsysProcess
                                 # fixes vs. our prior 3.28.3 — should
                                 # close out the parallel-build pipe-
                                 # leak hang seen on jpegturbo.
                                 revision="v3.31.12",
                                 md5val="8968437294e7cb7dafca802a80cb9da6",
                                 recursive=False)

    def areRequiredSourceFilesPresent(self):
        return (self.source_root/"CMakeLists.txt").exists() \
           and (self.source_root/"bootstrap").exists()

    def areRequiredBinaryFilesPresent(self):
        return (path.bin()/"cmake").exists()
