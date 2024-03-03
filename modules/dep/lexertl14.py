###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, path

###############################################################################

class lexertl14(dep.StdProvider):
  name = "lexertl14"
  def __init__(self):
    super().__init__(lexertl14.name)
    self.declareDep("cmake")
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
    build_src = self.build_src/"include"
    X = """
from conan import ConanFile
from conan.tools.cmake import CMake, cmake_layout
class LexerTL14Conan(ConanFile):
  name = "lexertl14"
  version = "tweakoz-obt"
  license = "<License here>"
  author = "<Your Name> <Your Email>"
  url = "https://github.com/tweakoz/lexertl14"
  description = "<Description of lexertl14 here>"
  topics = ("<Put some tag here>", "<Put another tag here>")
  settings = "os", "compiler", "build_type", "arch"
  exports_sources = ["include/*"]  # Adjust the pattern to match your source directory structure

  def layout(self):
    cmake_layout(self)

  def build(self):
    cmake = CMake(self)
    cmake.configure()
    cmake.build()

  def package(self):
    self.copy("*", dst="include", src="%s")  # Adjust 'src' to the correct source subdirectory if needed

  def package_info(self):
    self.cpp_info.libs = ["lexertl14"]
      """ % build_src

    return X
  #######################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.includes()/"lexertl"/"char_traits.hpp").exists()
