###############################################################################
# Orkid Build System
# Copyright 2010-2026, Michael T. Mayers
# Published under the GPL 2.0 license
###############################################################################
"""MaterialX (ASWF) shared libraries, standard data library and Python package.

Builds Core/Format, the shader generators (GLSL, MSL, OSL, MDL, Slang; codegen
only - no OSL/MDL runtimes needed) and the Render modules. No OIIO/OCIO, viewer,
graph editor or tests. Shared libraries are required by USD.
Install layout: lib/libMaterialX*, include/MaterialX*, lib/cmake/MaterialX
(MaterialX_DIR), <stage>/libraries (standard .mtlx data; MaterialX finds it by
walking up from its module path), and the MaterialX package in pyvenv site-packages.
"""
import re
import subprocess
from obt import dep, host, path, log
from obt.dependency_artifacts import defines_version, cmake_version, python_extension_suffix

VERSION = "1.39.5"
REVISION = "7b64921ef1d42f2d57871e9d2c43dc11f041f26b"  # refs/tags/v1.39.5 (lightweight tag)
# Python bindings use the bundled pybind11 3.0.1, which supports free-threaded 3.14t.
BUILD_PYTHON = True


class _Fetcher(dep.GithubFetcher):
  # Core needs no submodules (.gitmodules only lists viewer/graph-editor UI deps).
  def __init__(self):
    super().__init__(name="materialx", repospec="AcademySoftwareFoundation/MaterialX",
                     revision="v" + VERSION, recursive=False, disable_tarball=True)

  def fetch(self, dest):
    if not (dest/".git").exists() and not super().fetch(dest):
      return False
    try:
      actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=dest, text=True).strip()
      if actual != REVISION:
        raise RuntimeError("MaterialX checkout differs from the pinned v%s revision: %s" % (VERSION, actual))
      return True
    except (subprocess.CalledProcessError, RuntimeError) as error:
      print("MaterialX fetch failed:", error)
      return False


def _python_site_packages():
  return dep.instance("python").site_packages_dir


class materialx(dep.StdProvider):
  name = "materialx"
  VERSION = VERSION

  def __init__(self):
    super().__init__(self.name)
    self.setSourceRoot(path.builds()/self.name/("materialx-" + VERSION))
    self.declareDep("cmake")
    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder.setCmVars({
      "MATERIALX_BUILD_SHARED_LIBS": "ON",
      "MATERIALX_BUILD_MONOLITHIC": "OFF",
      "MATERIALX_BUILD_GEN_GLSL": "ON",
      "MATERIALX_BUILD_GEN_MSL": "ON",
      "MATERIALX_BUILD_GEN_OSL": "ON",
      "MATERIALX_BUILD_GEN_MDL": "ON",
      "MATERIALX_BUILD_GEN_SLANG": "ON",
      "MATERIALX_BUILD_RENDER": "ON",
      "MATERIALX_BUILD_OIIO": "OFF",
      "MATERIALX_BUILD_OCIO": "OFF",
      "MATERIALX_BUILD_VIEWER": "OFF",
      "MATERIALX_BUILD_GRAPH_EDITOR": "OFF",
      "MATERIALX_BUILD_TESTS": "OFF",
      "MATERIALX_BUILD_DOCS": "OFF",
      "MATERIALX_BUILD_JS": "OFF",
      "MATERIALX_BUILD_USE_CCACHE": "OFF",
      # Sample materials/images for the viewer; not needed by consumers.
      "MATERIALX_INSTALL_RESOURCES": "OFF",
      "MATERIALX_INSTALL_STDLIB_PATH": "libraries",
      "MATERIALX_INSTALL_LIB_PATH": "lib",
      "MATERIALX_INSTALL_INCLUDE_PATH": "include",
      "CMAKE_PREFIX_PATH": str(path.stage()),
      "CMAKE_IGNORE_PATH": "/opt/homebrew;/opt/homebrew/lib;/opt/homebrew/include",
    })
    if BUILD_PYTHON:
      self.declareDep("python")
      self._builder.requires(["python"])
      python = dep.instance("python")
      self._builder.setCmVars({
        "MATERIALX_BUILD_PYTHON": "ON",
        "MATERIALX_INSTALL_PYTHON": "ON",
        "MATERIALX_PYTHON_EXECUTABLE": python.executable,
        # Bundled pybind11 runs legacy FindPythonInterp/Libs from this (modern
        # Python_* hints are ignored); it also gates upstream's post-install
        # `pip install` of <stage>/python into the target site-packages.
        "PYTHON_EXECUTABLE": python.executable,
        # Never pick up a differently-versioned staged pybind11 package.
        "MATERIALX_PYTHON_PYBIND11_DIR": str(self.source_root/"source"/"PyMaterialX"/"External"/"PyBind11"),
      })
    else:
      self._builder.setCmVar("MATERIALX_BUILD_PYTHON", "OFF")

  @property
  def _fetcher(self):
    return _Fetcher()

  def areRequiredSourceFilesPresent(self):
    if not (self.source_root/"CMakeLists.txt").exists():
      return False
    try:
      head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.source_root,
                                     text=True, stderr=subprocess.DEVNULL).strip()
      return head == REVISION
    except (OSError, subprocess.CalledProcessError):
      return False

  def _python_module_path(self):
    suffix = python_extension_suffix(dep.instance("python").executable)
    return _python_site_packages()/"MaterialX"/("PyMaterialXCore" + suffix)

  def areRequiredBinaryFilesPresent(self):
    ext = self.shlib_extension
    if not all((path.libs()/("libMaterialX%s.%s" % (lib, ext))).is_file()
               for lib in ("Core", "Format", "GenShader", "GenGlsl", "GenMsl", "GenOsl")):
      return False
    header = path.includes()/"MaterialXCore"/"Generated.h"
    if not (defines_version(header, "MATERIALX_", VERSION.rsplit(".", 1)[0], "_VERSION")
            and _defines_build_version(header, VERSION.rsplit(".", 1)[1])
            and (path.includes()/"MaterialXCore"/"Document.h").is_file()
            and cmake_version(path.libs()/"cmake"/"MaterialX"/"MaterialXConfigVersion.cmake", VERSION)
            and (path.stage()/"libraries"/"targets").is_dir()):
      return False
    if not BUILD_PYTHON:
      return True
    try:
      return self._python_module_path().is_file()
    except (OSError, RuntimeError, subprocess.SubprocessError):
      return False

  @property
  def should_build(self):
    return super().should_build or not self.areRequiredBinaryFilesPresent()

  def env_init(self):
    log.sdk_announce("registering MaterialX SDK(%s)" % VERSION)


def _defines_build_version(filename, build):
  # MaterialX names its third component BUILD, which defines_version does not cover.
  try:
    text = filename.read_text()
  except (OSError, UnicodeError):
    return False
  match = re.search(r'^\s*#\s*define\s+MATERIALX_BUILD_VERSION\s+(\d+)\b', text, re.MULTILINE)
  return bool(match) and int(match.group(1)) == int(build)
