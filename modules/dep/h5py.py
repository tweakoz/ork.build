###############################################################################
# Orkid Build System
# Copyright 2010-2026, Michael T. Mayers
# email: michael@tweakoz.com
# Published under GPL 2.0 license
###############################################################################
# h5py — python bindings for HDF5, installed into the staging pyvenv.
#
# Built FROM SOURCE against the OBT-built HDF5 (modules/dep/hdf5.py), never
# from a PyPI wheel: those wheels bundle their own libhdf5 copy, which would
# put a second, unmanaged HDF5 in the process alongside the staging one.
#
# The HDF5 dep installs its headers to <staging>/include/hdf5 (keeping them out
# of the shared flat include dir) while its libraries stay in <staging>/lib, so
# there is no single prefix with include/ + lib/ under it and h5py's HDF5_DIR
# pin cannot be used. h5py's other documented form is the split pair
# HDF5_INCLUDEDIR + HDF5_LIBDIR (docs/build.rst). The two forms are mutually
# exclusive: setup_configure.py raises "Specify only one of ..." if HDF5_DIR is
# set alongside either of them, so HDF5_DIR must stay unset here.
#
# Pinned to 3.16.0. Consumers: SOFA/HRTF dataset prep — a SOFA file is plain
# HDF5, so h5py alone reads it; no netCDF4 / sofar needed.
###############################################################################

import glob
from yarl import URL
from obt import dep, host, path, log
from obt.command import Command

NAME     = "h5py"
VERSION  = "3.16.0"
BASENAME = "h5py-%s" % VERSION
FILENAME = "%s.tar.gz" % BASENAME
URL_BASE = "https://files.pythonhosted.org/packages/db/33/acd0ce6863b6c0d7735007df01815403f5589a21ff8c2e1ee2587a38f548"
MD5      = "c4dfd49d4282fecd5eeff10f4cd388c7"

###############################################################################

def _build_env():
    HDF5 = dep.instance("hdf5")
    env = {
        # split pin — headers and libs do not share a prefix (see header note).
        # HDF5_DIR must NOT be set alongside these.
        "HDF5_DIR": None,
        "HDF5_PKGCONFIG_NAME": None,
        "HDF5_INCLUDEDIR": str(HDF5.include_dir),
        "HDF5_LIBDIR":     str(HDF5.lib_dir),
        # skip h5py's own version probe (it compiles and runs a test binary)
        "HDF5_VERSION": str(HDF5.VERSION),
        # keep the feature set deterministic: without these, h5py's configure
        # step auto-enables the S3 / direct VFDs if it happens to find libcurl
        # + openssl, which drags extra link deps into the extension.
        "H5PY_ROS3":       "0",
        "H5PY_DIRECT_VFD": "0",
    }
    # setuptools does not add an rpath for library_dirs. Belt-and-braces for
    # the case where libhdf5's install_name is @rpath-relative (obt's macho
    # fixup pass rewrites staging dylibs to @rpath on a fresh staging).
    rpath_flag = "-Wl,-rpath,%s" % str(path.libs())
    env["LDFLAGS"] = rpath_flag
    return env

###############################################################################

def _build_wheel():
    PYTHON = dep.instance("python")
    src    = path.builds()/NAME/BASENAME
    rc = Command([str(PYTHON.executable), "-m", "pip", "wheel",
                  "--no-deps", "-w", str(src/"dist"), "."],
                 environment=_build_env(),
                 working_dir=src).exec()
    return rc == 0

###############################################################################

def _install_wheel():
    PYTHON = dep.instance("python")
    src    = path.builds()/NAME/BASENAME
    wheels = sorted(glob.glob(str(src/"dist"/"h5py-*.whl")))
    if not wheels:
        log.marker("no h5py wheel under %s/dist/" % src)
        return False
    whl = wheels[-1]
    log.marker("installing h5py wheel: %s" % whl)
    rc = Command([str(PYTHON.executable), "-m", "pip", "install",
                  "--no-deps", "--force-reinstall", whl]).exec()
    return rc == 0

###############################################################################

class h5py(dep.StdProvider):
    name = NAME

    def __init__(self):
        super().__init__(NAME)
        self.VERSION = VERSION
        self.declareDep("python")
        self.declareDep("pydefaults")   # numpy — h5py's runtime requirement
        self.declareDep("hdf5")
        if path.has_deployment_marker:
            return
        # sdist extracts to builds/h5py/h5py-X.Y.Z/
        self.setSourceRoot(path.builds()/NAME/BASENAME)
        self._builder = self.createBuilder(dep.CustomBuilder)
        self._builder._cleanbuildcommands += [_build_wheel]
        self._builder._incrbuildcommands  += [_build_wheel]
        self._builder._installcommands    += [_install_wheel]

    def __str__(self):
        return "h5py (pypi-source-%s)" % VERSION

    @property
    def _fetcher(self):
        f = dep.WgetFetcher(NAME)
        f._url     = URL(URL_BASE)/FILENAME
        f._fname   = FILENAME
        f._arctype = "tgz"
        f._md5     = MD5
        return f

    def areRequiredSourceFilesPresent(self):
        return (self.source_root/"setup.py").exists()

    def areRequiredBinaryFilesPresent(self):
        PYTHON = dep.instance("python")
        return (PYTHON.site_packages_dir/"h5py"/"version.py").exists()
