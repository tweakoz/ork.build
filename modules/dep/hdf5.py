###############################################################################
# Orkid Build System
# Copyright 2010-2026, Michael T. Mayers
# email: michael@tweakoz.com
# Published under GPL 2.0 license
###############################################################################
# HDF5 — hierarchical data format C library.
#
# Needed because SOFA (Spatially Oriented Format for Acoustics, the HRTF
# dataset container) files are plain HDF5. The python side lives in the
# h5py dep, which links against THIS build — see modules/dep/h5py.py.
#
# Pinned to 2.1.1 (released 2026-03-23). The 2.x line dropped autotools, so
# this is a CMake-only build. 2.1.x is the series upstream h5py 3.16 wheels
# are built against — this build produces libhdf5.320.1.1, the same soversion
# line (320) as the libhdf5 those wheels bundle. 2.2.0 exists but was two
# weeks old at time of writing — not chosen.
#
# Option notes:
#  - HDF5_ENABLE_ZLIB_SUPPORT defaults OFF in 2.x. SOFA files in the wild are
#    commonly deflate-compressed, so it is forced ON here. With
#    HDF5_ALLOW_EXTERNAL_SUPPORT=NO, cmake uses find_package(ZLIB) instead of
#    downloading and building its own zlib.
#  - On macOS the ZLIB_* vars are pinned to the SDK so FindZLIB cannot latch
#    onto /opt/homebrew/lib/libz.dylib (same guard libarchive.py uses for lz4).
#  - HDF5_INSTALL_INCLUDE_DIR puts the ~65 public headers (H5*.h, hdf5.h,
#    hdf5_hl.h) in <prefix>/include/hdf5 instead of dumping them flat into the
#    shared staging include dir. It is HDF5's own install-dir knob and is
#    honored as a plain prefix-relative path (config/HDFMacros.cmake, macro
#    HDF_DIR_PATHS: any preset value wins, else "include"). Note that
#    CMAKE_INSTALL_INCLUDEDIR is NOT consulted unless HDF5_USE_GNU_DIRS=ON,
#    which would also relocate the cmake/doc/data dirs — so the HDF5_ var is
#    the surgical one. It feeds the header install() destination, the exported
#    target INTERFACE include dir, and hdf5.pc's includedir alike. Libraries,
#    tools and the cmake package files keep their existing locations.
#  - CMAKE_INSTALL_NAME_DIR is forced to the absolute staging lib dir,
#    overriding CMakeBuilder's @executable_path/../lib default. The main
#    consumer is a python extension (h5py) loaded by the pyvenv interpreter at
#    <staging>/pyvenv/bin/python, for which @executable_path/../lib resolves to
#    <staging>/pyvenv/lib — the wrong place. Absolute matches what liblzma
#    (also consumed by the pyvenv python) already does in the staging.
###############################################################################

VERSION  = "2.1.1"
BASENAME = "hdf5-%s" % VERSION
FILENAME = "%s.tar.gz" % BASENAME
URL_BASE = "https://github.com/HDFGroup/hdf5/releases/download/%s" % VERSION
MD5      = "105d909d2d11374c6e78fda414802e93"

from yarl import URL
from obt import dep, host, path

###############################################################################

class hdf5(dep.StdProvider):
    name = "hdf5"

    def __init__(self):
        super().__init__(hdf5.name)
        self.VERSION = VERSION
        self.declareDep("cmake")
        # Tarball extracts to builds/hdf5/hdf5-X.Y.Z/, not builds/hdf5/.
        self.setSourceRoot(path.builds()/hdf5.name/BASENAME)
        self._builder = self.createBuilder(dep.CMakeBuilder)
        self._builder.setCmVars({
            # headers go to <prefix>/include/hdf5, not flat into <prefix>/include
            "HDF5_INSTALL_INCLUDE_DIR":   "include/hdf5",
            "BUILD_SHARED_LIBS":          "ON",
            "BUILD_STATIC_LIBS":          "OFF",
            "BUILD_TESTING":              "OFF",
            "HDF5_BUILD_EXAMPLES":        "OFF",
            "HDF5_BUILD_TOOLS":           "ON",   # h5dump / h5ls / h5repack
            "HDF5_BUILD_HL_LIB":          "ON",   # h5py links libhdf5_hl
            "HDF5_BUILD_CPP_LIB":         "OFF",
            "HDF5_BUILD_FORTRAN":         "OFF",
            "HDF5_BUILD_JAVA":            "OFF",
            "HDF5_BUILD_DOC":             "OFF",
            "HDF5_ENABLE_ZLIB_SUPPORT":   "ON",
            "HDF5_ENABLE_SZIP_SUPPORT":   "OFF",
            "HDF5_ENABLE_PLUGIN_SUPPORT": "OFF",
            "HDF5_ENABLE_PARALLEL":       "OFF",
            "HDF5_ENABLE_THREADSAFE":     "OFF",
            # never fetch/build zlib or libaec itself — use the system one
            "HDF5_ALLOW_EXTERNAL_SUPPORT": "NO",
            "ZLIB_USE_EXTERNAL":           "OFF",
            "SZIP_USE_EXTERNAL":           "OFF",
        })
        if host.IsOsx:
            sdkdir = path.osx_sdkdir()
            self._builder.setCmVars({
                # Apple Clang accepts _Float16, but the SDK float.h lacks
                # FLT16_MAX and related macros required by this HDF5 feature.
                "HDF5_ENABLE_NONSTANDARD_FEATURE_FLOAT16": "OFF",
                "CMAKE_INSTALL_NAME_DIR": str(path.libs()),
                "ZLIB_INCLUDE_DIR":       "%s/usr/include" % sdkdir,
                "ZLIB_LIBRARY":           "%s/usr/lib/libz.tbd" % sdkdir,
            })

    def __str__(self):
        return "hdf5 (hdfgroup-source-%s)" % VERSION

    ###########################################################################
    # _fetcher is a property: must be built fully in the getter, since
    # writes to a property's return value are discarded.
    ###########################################################################

    @property
    def _fetcher(self):
        f = dep.WgetFetcher(hdf5.name)
        f._url     = URL(URL_BASE)/FILENAME
        f._fname   = FILENAME
        f._arctype = "tgz"
        f._md5     = MD5
        return f

    def areRequiredSourceFilesPresent(self):
        return (self.source_root/"CMakeLists.txt").exists()

    def areRequiredBinaryFilesPresent(self):
        return (path.libs()/("libhdf5.%s" % self.shlib_extension)).exists() \
           and (path.includes()/"hdf5"/"hdf5.h").exists()

    ###########################################################################
    # consumer-facing properties. include_dir and lib_dir are NOT siblings
    # under a single prefix any more, so consumers must pin them separately
    # (h5py uses HDF5_INCLUDEDIR + HDF5_LIBDIR, not HDF5_DIR).
    ###########################################################################

    @property
    def root(self):
        return path.prefix()

    @property
    def include_dir(self):
        return path.includes()/"hdf5"

    @property
    def lib_dir(self):
        return path.libs()
