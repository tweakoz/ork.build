###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from ork import dep, host, command, path

###############################################################################

class nvtt(dep.StdProvider):

  def __init__(self):
    name = "nvtt"
    super().__init__(name)
    self._fetcher = dep.GitFetcher(name)
    self._fetcher._git_url = "https://github.com/tweakoz/nvidia-texture-tools"
    self._fetcher._revision = "toz_orkdotbuild"
    ###########################################
    ## nvtt installs with wrong rpath install name
    ##  on mac, so we fix it up here..
    ###########################################
    class FixOsx(dep.CMakeBuilder):
      def __init__(self,name):
        super().__init__(name)
      def install(self,blddir):
        dylibname = "libnvtt.dylib"
        dylibpath = self.build_dest/"src"/"nvtt"/dylibname
        nvcpath = self.build_dest/"src"/"nvtt"/dylibname
        retc = command.run(["install_name_tool","-id",
                            "@rpath/../lib/"+dylibname,
                            dylibpath])
        success = retc==0
        if success:
          success = super().install(blddir)
        return success
    ###########################################
    builder_class = dep.switch(linux=dep.CMakeBuilder,
                               macos=FixOsx)
    self._builder = builder_class(name)
    self._builder.build_dest = self.build_dest
    ###########################################
    self._builder.requires(["openexr"])
    self._builder._cmakeenv = {
      "BUILD_SHARED_LIBS": "ON",
    }
    ############################################
    # because, cuda 10 requires it - todo - make dynamic
    ############################################
    if host.IsLinux:
        self._builder.setCmVars({
          "CMAKE_CXX_COMPILER": "g++-8",
          "CMAKE_C_COMPILER": "gcc-8" })
    elif host.IsOsx:
        self._builder.setCmVars({
          "CMAKE_INSTALL_NAME_DIR": "@executable_path/../lib/",
          "CMAKE_BUILD_WITH_INSTALL_RPATH": "ON"})
