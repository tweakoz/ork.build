###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os
from obt import dep, path, template, env, command, conan, subspace, host, target

CONAN_FILE = """
from conan import ConanFile
from conan.tools.cmake import CMake, cmake_layout, CMakeToolchain
from conan.tools.files import get
import os

class LexerTL14Conan(ConanFile):
    name = "lexertl14"
    version = "tweakoz-obt"
    license = "<License here>"
    author = "<Your Name> <Your Email>"
    url = "https://github.com/tweakoz/lexertl14"
    description = "<Description of lexertl14 here>"
    topics = ("<Put some tag here>", "<Put another tag here>")
    settings = "os", "compiler", "build_type", "arch"

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()

    def layout(self):
        cmake_layout(self)

    def source(self):
        get(self, "https://github.com/tweakoz/lexertl14/archive/refs/heads/toz-oct16.zip", destination=self.source_folder, strip_root=True)

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package_info(self):
        self.cpp_info.libs = ["lexertl14"]
"""

###############################################################################

class lexertl14(dep.StdProvider):
  name = "lexertl14"
  def __init__(self):
    super().__init__(lexertl14.name,subspace_vif=2)
    self.scope = dep.ProviderScope.SUBSPACE    
    self.declareDep("cmake")
    tgt = target.current()
    ############################################
    if tgt != None and tgt.os=="ios":
    ############################################
      self._builder = self.createBuilder(dep.ConanBuilder)
      lexertl14_dir = path.conan_prefix() / "lexertl14"
      lexertl14_dir.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists
      # write conanfile.py
      lrtl_output = lexertl14_dir / "conanfile.py"
      with open(lrtl_output, "w") as f:
          f.write(self._conanfile)  
      #
      self._builder._working_dir = lexertl14_dir
      os.chdir(str(lexertl14_dir))
      #conan export . lexertl14/tweakoz-obt@user/channel
      the_environ = os.environ.copy()
      the_environ.update(conan.environment())
      self._builder._environment = the_environ
      self._builder._cmdlist = \
        ["conan","export",".",
         "--user=user",
         "--channel=channel"]
      self._builder._cmdlist2 = \
        ["conan", "create", ".",
         f"--profile:host={path.subspace_dir()}/ios.host.profile",
         f"--profile:build={path.subspace_dir()}/ios.build.profile",
         "--user=user",
         "--channel=channel",
         "--build=missing"]
    ############################################
    else:
    ############################################
      self._builder = self.createBuilder(dep.CMakeBuilder)
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=lexertl14.name,
                             repospec="tweakoz/lexertl14",
                             revision="toz-oct16",
                             recursive=False)

  #######################################################################
  @property
  def _conanfile(self):
    return CONAN_FILE
  #######################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.subspace_includes()/"lexertl"/"char_traits.hpp").exists()
