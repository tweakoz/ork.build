###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, tarfile
from obt import dep, host, path, pathtools, git, cmake, make
from obt.deco import Deco
from obt.wget import wget
from obt.command import Command

deco = Deco()

VERSION = "4.11.0"
###############################################################################

class opencv(dep.StdProvider):
  name = "opencv"
  def __init__(self): ############################################
    super().__init__(opencv.name)
    self.declareDeps(["pybind11","opencv_contrib"])
    self.EXR = self.declareDep("openexr")
    # opencv.py builds the OpenCV C++ SDK only — headers + dylibs into
    # $OBT_STAGE, consumed by dependent native code. The python cv2
    # module is NOT built here; it is provided by the separate
    # `opencv_python` dep (the tweakoz/opencv-python fork, pip-installed so
    # it carries proper dist metadata). A C++-only build needs no python.
    self._builder = self.createBuilder(dep.CMakeBuilder)

    cmakeEnv = {
      "CMAKE_BUILD_TYPE": "RELEASE",
      "INSTALL_C_EXAMPLES": "ON",
      "INSTALL_PYTHON_EXAMPLES": "OFF",
      "ENABLE_PRECOMPILED_HEADERS": "OFF",
      "WITH_TBB": "OFF",
      "WITH_GDAL": "OFF",
      "WITH_QT": "OFF",
      "WITH_GTk": "ON",
      "WITH_GTK_2_X": "OFF",
      "WITH_OPENGL": "OFF",
      "WITH_CAROTENE": "OFF",
      "WITH_FFMPEG": "OFF",
      "WITH_GSTREAMER": "OFF",
      "WITH_FREETYPE":"OFF",
      "OPENCV_EXTRA_MODULES_PATH": "../../opencv_contrib/modules",
      "WITH_OPENEXR": "OFF",
      "BUILD_opencv_gapi":"OFF", # fails to build on ub22-aarch64
      # python cv2 is built by the `opencv_python` dep, not here.
      "BUILD_opencv_python2":"OFF",
      "BUILD_opencv_python3":"OFF",
      "BUILD_EXAMPLES": "OFF",
    }
    if host.IsLinux:
      cmakeEnv["WITH_V4L"]="ON"
    self._builder.setCmVars(cmakeEnv)

  ########################################################################

  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=opencv.name,
                             repospec="tweakoz/opencv",
                             revision=VERSION,
                             recursive=False)

  ########################################################################

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.includes()/"opencv4"/"opencv2"/"core.hpp").exists()

  ########################################################################

  def deployment_fixup(self, deploy_root):
    """Rewrite cv2 config files + setup_vars_opencv4.sh to use relative paths.

    The upstream OpenCV CMake takes PYTHON3_PACKAGES_PATH (absolute on our
    builds because it's the dev's staging site-packages) and substitutes it
    verbatim into setup_vars_opencv4.sh's template: the result is the
    malformed `$SCRIPT_DIR//Users/michael/.staging-mar25/pyvenv/lib/.../site-packages`
    line you see in shipped bundles. The absolute path is frozen at the
    dev's staging location and won't be reachable on any user machine;
    the leading `$SCRIPT_DIR/` prefix also means the concatenation is
    garbage regardless of where the bundle ends up. Overwrite the file
    with a sibling-relative form that follows the same convention as the
    DYLD_LIBRARY_PATH line above it.
    """
    import glob
    for cv2_dir in glob.glob(f"{deploy_root}/pyvenv/lib/python*/site-packages/cv2"):
      p = path.Path(cv2_dir)
      # config.py: BINARIES_PATHS → .staging/lib (5 parents up from cv2/)
      (p/"config.py").write_text(
        "import pathlib\n"
        "BINARIES_PATHS = [str(pathlib.Path(__file__).parents[5] / 'lib')] + BINARIES_PATHS\n")
      # config-X.Y.py: PYTHON_EXTENSIONS_PATHS → cv2/python-X.Y/
      for cfg in p.glob("config-*.py"):
        pydir = cfg.stem.replace("config-", "python-")
        cfg.write_text(
          "import pathlib\n"
          f"PYTHON_EXTENSIONS_PATHS = [str(pathlib.Path(__file__).parent / '{pydir}')] + PYTHON_EXTENSIONS_PATHS\n")

    # ---- setup_vars_opencv4.sh: rewrite the PYTHONPATH line -----------
    # The file lives at $deploy_root/bin/. Discover pyvenv's actual site-
    # packages directory via glob (python version varies between builds).
    setup_vars = path.Path(f"{deploy_root}/bin/setup_vars_opencv4.sh")
    if setup_vars.exists():
      pyver_dirs = glob.glob(f"{deploy_root}/pyvenv/lib/python*/site-packages")
      if pyver_dirs:
        # pyver_dirs[0] = <root>/pyvenv/lib/pythonX.Y/site-packages
        # .parent        = <root>/pyvenv/lib/pythonX.Y
        # .parent.name   = "pythonX.Y"
        pyver_name = path.Path(pyver_dirs[0]).parent.name  # pythonX.Y
        rel = f"../pyvenv/lib/{pyver_name}/site-packages"
        setup_vars.write_text(
          "#!/bin/bash\n"
          "#\n"
          "# OpenCV environment setup. Regenerated by deployment_fixup to use\n"
          "# $SCRIPT_DIR-relative paths; upstream OpenCV's template bakes in\n"
          "# the build-time PYTHON3_PACKAGES_PATH which is absolute on our\n"
          "# builds and breaks relocation.\n"
          "\n"
          "SCRIPT_DIR=\"$( cd \"$( dirname \"${BASH_SOURCE[0]}\" )\" >/dev/null && pwd )\"\n"
          "\n"
          "[[ ! \"${OPENCV_QUIET}\" ]] && ( echo \"Setting vars for OpenCV " + VERSION + "\" )\n"
          "export DYLD_LIBRARY_PATH=\"$SCRIPT_DIR/../lib:${DYLD_LIBRARY_PATH:-}\"\n"
          "\n"
          "if [[ ! \"$OPENCV_SKIP_PYTHON\" ]]; then\n"
          f"  PYTHONPATH_OPENCV=\"$SCRIPT_DIR/{rel}\"\n"
          "  [[ ! \"${OPENCV_QUIET}\" ]] && ( echo \"Append PYTHONPATH: ${PYTHONPATH_OPENCV}\" )\n"
          "  export PYTHONPATH=\"${PYTHONPATH_OPENCV}:${PYTHONPATH:-}\"\n"
          "fi\n"
          "\n"
          "# Don't exec in \"sourced\" mode\n"
          "if [[ \"${BASH_SOURCE[0]}\" == \"${0}\" ]]; then\n"
          "  if [[ $# -ne 0 ]]; then\n"
          "    [[ ! \"${OPENCV_QUIET}\" && \"${OPENCV_VERBOSE}\" ]] && ( echo \"Executing: $*\" )\n"
          "    exec \"$@\"\n"
          "  fi\n"
          "fi\n")
