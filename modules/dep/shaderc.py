###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, tarfile
from obt import dep, host, path

###############################################################################

class shaderc(dep.StdProvider):
  name = "shaderc"
  def __init__(self): ############################################
    super().__init__(shaderc.name)
    self.VERSION = "v2025.1"
    self.declareDep("cmake")
    self._builder = self.createBuilder(dep.CMakeBuilder)
    BUILDS = path.builds()
    self.SHADERC_DIR = BUILDS/"shaderc"
    self.SHADERC_SPIRV_TOOLS_DIR = BUILDS/"shaderc"/"external"/"spirv-tools"
    self.SHADERC_SPIRV_HEADERS_DIR = BUILDS/"shaderc"/"external"/"spirv-headers"
    self.SHADERC_GLSLANG_DIR = BUILDS/"shaderc"/"external"/"glslang"
    self._builder.setCmVars({
        "SHADERC_SKIP_TESTS": "ON",
        "SHADERC_SPIRV_TOOLS_DIR": self.SHADERC_SPIRV_TOOLS_DIR,
        "SHADERC_SPIRV_HEADERS_DIR": self.SHADERC_SPIRV_HEADERS_DIR,
        "SHADERC_GLSLANG_DIR": self.SHADERC_GLSLANG_DIR        
    })
  ########################################################################
  def __str__(self): 
    return "shaderc (github-%s)" % self.VERSION
  ########################################################################
  @property
  def _fetcher(self):
    f = dep.CompositeFetcher("shaderc-composite")
    f1 = dep.GithubFetcher(name="shaderc",
                           repospec="tweakoz/shaderc",
                           revision=self.VERSION,
                           recursive=False,
                           dest_dir_override = self.SHADERC_DIR)
    f2 = dep.GithubFetcher(name="shaderc-spirvtools",
                           repospec="tweakoz/SPIRV-Tools",
                           revision="vulkan-sdk-1.4.309.0",
                           recursive=False,
                           dest_dir_override = self.SHADERC_SPIRV_TOOLS_DIR)
    f3 = dep.GithubFetcher(name="shaderc-spirvheaders",
                           repospec="tweakoz/SPIRV-Headers",
                           revision="vulkan-sdk-1.4.309.0",
                           recursive=False,
                           dest_dir_override = self.SHADERC_SPIRV_HEADERS_DIR)
    f4 = dep.GithubFetcher(name="shaderc-glslang",
                           repospec="tweakoz/glslang",
                           revision="vulkan-sdk-1.4.309.0",
                           recursive=False,
                           dest_dir_override = self.SHADERC_GLSLANG_DIR)
    f.addSubFetcher(f1)
    f.addSubFetcher(f2)
    f.addSubFetcher(f3)
    f.addSubFetcher(f4)
    return f 
  ########################################################################
  def linkenv(self):
    LIBS = ["shaderc"]
    return {
        "LIBS": LIBS,
        "LFLAGS": ["-l%s"%item for item in LIBS]
    }
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.includes()/"shaderc"/"shaderc.h").exists()
