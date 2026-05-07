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
            "--",
            "-DCMAKE_USE_OPENSSL=OFF",          # avoid OpenSSL pull during bootstrap
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
                                 revision="v3.28.3",
                                 recursive=False)

    def areRequiredSourceFilesPresent(self):
        return (self.source_root/"CMakeLists.txt").exists() \
           and (self.source_root/"bootstrap").exists()

    def areRequiredBinaryFilesPresent(self):
        return (path.bin()/"cmake").exists()
