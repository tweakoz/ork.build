###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from ork import dep, host, command, path

###############################################################################

class glfw(dep.StdProvider):

  def __init__(self):
    name = "glfw"
    super().__init__(name)
    self._fetcher = dep.GitFetcher(name)
    self._fetcher._git_url = "https://github.com/glfw/glfw"
    self._fetcher._revision = "master"
    ###########################################
    ## GLFW installs with wrong rpath install name
    ##  on mac, so we fix it up here..
    ###########################################
    class FixOsx(dep.CMakeBuilder):
      def __init__(self,name):
        super().__init__(name)
      def install(self,blddir):
        success = super().install(blddir)
        if success:
          dylibname = "libglfw.3.dylib"
          retc = command.run(["install_name_tool","-id",
                              "@rpath/"+dylibname,path.libs()/dylibname])
          success = retc==0
        return success
    ###########################################
    builder_class = dep.switch(linux=dep.CMakeBuilder,
                               macos=FixOsx)
    self._builder = builder_class(name)
    #self._builder.setCmVar("GLFW_VULKAN_STATIC","TRUE")
    ###########################################
