###############################################################################
# Orkid Build System
# Copyright 2010-2026, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
# opencv-python dep — sourced from the tweakoz fork at
# git@github.com:tweakoz/opencv-python.git, branch obt-cp314t-no-homebrew.
# That branch carries two patches that PyPI's opencv-python wheels lack:
#   1. PYTHON3_LIMITED_API=OFF — required for Python 3.14 free-threaded
#      (cp314t) builds, where the limited API is not yet supported.
#   2. WITH_AVIF=OFF — prevents cmake from auto-linking against
#      /opt/homebrew/lib/libavif.dylib if present, which would leak
#      homebrew refs into cv2.so.
###############################################################################

import os, glob
from obt import dep, host, path, pathtools
from obt.command import Command

NAME = "opencv_python"
REPO = "tweakoz/opencv-python"
REVISION = "obt-cp314t-no-homebrew"

###############################################################################

class opencv_python(dep.StdProvider):
  def __init__(self):
    super().__init__(NAME)
    if path.has_deployment_marker:
      return
    # pydefaults installs numpy + scikit-build + setuptools, all required to
    # build the opencv-python wheel. Declaring it here ensures order.
    self.declareDep("pydefaults")
    self._builder = self.createBuilder(dep.CustomBuilder)
    # Single callable that runs the wheel build + install. Done as a
    # closure because self.source_root isn't populated until after fetch,
    # which is after __init__.
    self._builder._installcommands += [self._build_and_install_wheel]

  ########################################################################
  @property
  def _fetcher(self):
    # recursive=True so opencv/opencv_contrib/opencv_extra submodules come
    # along — required for the cmake build.
    return dep.GithubFetcher(name=NAME,
                             repospec=REPO,
                             revision=REVISION,
                             recursive=True)

  ########################################################################

  def _build_and_install_wheel(self):
    PYTHON = dep.instance("python")
    py = PYTHON.executable
    wheels_dir = path.builds()/NAME/"wheels"
    pathtools.mkdir(wheels_dir, clean=True, parents=True)

    # scikit-build leaves _skbuild/ in the source tree. Its CMakeCache.txt
    # hardcodes the numpy include path from the pip build env used that run.
    # pip build envs are ephemeral (random names), so on a later rebuild that
    # cached path is dead -> 'numpy/ndarrayobject.h not found'. Wipe it so
    # cmake reconfigures against the current build env.
    skbuild_dir = self.source_root/"_skbuild"
    if skbuild_dir.exists():
      Command(["/bin/rm", "-rf", str(skbuild_dir)]).exec()

    rc = Command([str(py), "-m", "pip", "wheel", "--no-deps",
                  "-w", str(wheels_dir), "."],
                 working_dir=self.source_root).exec()
    if rc != 0:
      print("opencv_python: pip wheel failed rc=%d" % rc)
      return False

    wheels = glob.glob(str(wheels_dir/"opencv_python-*.whl"))
    if not wheels:
      print("opencv_python: no wheel produced in %s" % wheels_dir)
      return False
    wheel = wheels[0]
    # Remove any pre-existing cv2/ before installing — e.g. one left by an
    # older opencv.py build that compiled the bindings. That cv2 had no pip
    # metadata, so pip's --force-reinstall cannot uninstall it and its
    # orphan files would shadow the freshly-installed wheel.
    stale_cv2 = PYTHON.site_packages_dir/"cv2"
    if stale_cv2.exists():
      Command(["/bin/rm", "-rf", str(stale_cv2)]).exec()
    rc = Command([str(py), "-m", "pip", "install",
                  "--force-reinstall", "--no-deps", wheel]).exec()
    if rc != 0:
      print("opencv_python: pip install %s failed rc=%d" % (wheel, rc))
      return False
    return True

  ########################################################################

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"setup.py").exists()

  def areRequiredBinaryFilesPresent(self):
    PYTHON = dep.instance("python")
    return (PYTHON.site_packages_dir/"cv2"/"__init__.py").exists()
