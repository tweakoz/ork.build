###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, host, command, path, pathtools

###############################################################################

class glfw(dep.StdProvider):
  name = "glfw"
  def __init__(self):
    super().__init__(glfw.name)
    ###########################################
    ## GLFW installs with wrong rpath install name
    ##  on mac, so we fix it up here..
    ###########################################
    class FixOsx(dep.CMakeBuilder):
      def __init__(self,name):
        super().__init__(name)
        self._cmakeenv["CMAKE_CXX_FLAGS"] = '"-D_GLFW_VULKAN_LIBRARY=MoltenVK"'
      def install(self,blddir):
        success = super().install(blddir)
        if success and host.IsOsx:
          dylibname = "libglfw.3.dylib"
          retc = command.run(["install_name_tool","-id",
                              "@rpath/"+dylibname,path.libs()/dylibname])
          success = retc==0
        return success
    ###########################################
    builder_class = dep.switch(linux=dep.CMakeBuilder,
                               macos=FixOsx)
    
    if builder_class == dep.CMakeBuilder:
      self.declareDep("cmake")


    self._builder = builder_class(glfw.name)
    
    def post_install():
      print("post installing GLFW!!")
      glad_srcdir = path.builds()/"glfw"/"deps"/"glad"
      glad_dstdir = path.includes()/"glad"
      pathtools.ensureDirectoryExists(glad_dstdir)
      for item in ["gl.h","khrplatform.h","vk_platform.h","vulkan.h"]:
        pathtools.copyfile(glad_srcdir/item,glad_dstdir/item)
      pass 

    self._builder._onPostInstall = post_install
    #self._builder.setCmVar("GLFW_VULKAN_STATIC","TRUE")
    ###########################################
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=glfw.name,
                             repospec="glfw/glfw",
                             revision="3.3.8",
                             recursive=False)

  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return path.decorate_obt_lib("glfw").exists()
