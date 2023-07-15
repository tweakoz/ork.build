###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, host, path, pathtools, command, env
import os
###############################################################################
class ue5_cesium(dep.StdProvider):
  name = "ue5_cesium"
  def __init__(self):
    super().__init__(ue5_cesium.name)
    #self._archlist = ["x86_64"]
    self.declareDep("cmake")
    self.UE5 = self.declareDep("ue5")
    UE5DIR = self.UE5.source_root
    UE5ENGDIR = UE5DIR/"Engine"

    self._osenv = dict()
    self._osenv["UNREAL_ENGINE_DIR"]=UE5DIR
    self._osenv["UNREAL_ENGINE_COMPILER_DIR"]=self.UE5.compiler_dir
    self._osenv["UNREAL_ENGINE_LIBCXX_DIR"]=UE5ENGDIR/"Source"/"ThirdParty"/"Unix"/"LibCxx"

    self._builder = self.createBuilder(dep.CMakeBuilder)
    self._builder._osenv = self._osenv

    self._builder._cmakeenv["CMAKE_TOOLCHAIN_FILE"]="unreal-linux-toolchain.cmake"
    self._builder._cmakeenv["CMAKE_POSITION_INDEPENDENT_CODE"]="ON"
    self._builder._cmakeenv["CMAKE_BUILD_TYPE"]="Debug"

    self.build_dest = self.source_root/"extern"/"build"
    self.build_working_dir = self.source_root/"extern"

    #####################################
    # install triangle
    #####################################

    def post_install():
      #print("post installing IGL!!")
      #igl_builddir = path.builds()/"igl"/".build"
      #pathtools.copyfile(igl_builddir/"lib"/"libtriangle.a",path.libs()/"libtriangle.a")
      #pathtools.copyfile(igl_builddir/"_deps"/"triangle-src"/"triangle.h",path.includes()/"triangle.h")
      cmdlist = ["cmake","--build","build","--target","install"]
      command.run(cmdlist,working_dir=self.source_root/"extern")
      pass

    self._builder._onPostInstall = post_install

    #####################################

  ########
  def on_build_shell(self):
    print(self._osenv)
    env.set("UNREAL_ENGINE_DIR",str(self.UE5.root_dir))
    env.set("UNREAL_ENGINE_COMPILER_DIR",str(self.UE5.compiler_dir))
    env.set("UNREAL_ENGINE_LIBCXX_DIR",str(self.UE5.engine_dir/"Source"/"ThirdParty"/"Unix"/"LibCxx"))
    env.set("CESIUM_FOR_UNREAL_DIR",str(self.source_root))

    shscr = '#!/usr/bin/env sh\n'
    shscr += 'cmake -B build -S . -DCMAKE_TOOLCHAIN_FILE="unreal-linux-toolchain.cmake" -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DCMAKE_BUILD_TYPE=Release\n'
    shscr +="cmake --build build --target install -j 16\n"
    #shscr +='cd $UNREAL_ENGINE_DIR/Engine/Build/BatchFiles\n'
    #shscr +='./RunUAT.sh BuildPlugin -Plugin="$CESIUM_FOR_UNREAL_DIR/CesiumForUnreal.uplugin" -Package="$CESIUM_FOR_UNREAL_DIR/../packages/CesiumForUnreal" -CreateSubFolder -TargetPlatforms=Linux\n'
    shscr +='$UNREAL_ENGINE_DIR/Engine/Build/BatchFiles/RunUAT.sh BuildPlugin -Plugin="$CESIUM_FOR_UNREAL_DIR/CesiumForUnreal.uplugin" -Package="$OBT_BUILDS/ue5pkg_CesiumForUnreal" -CreateSubFolder -TargetPlatforms=Linux\n'
    shscr +='mkdir -p $UNREAL_ENGINE_DIR/Engine/Plugins/Marketplace\n'
    shscr +='cp -r $OBT_BUILDS/ue5pkg_CesiumForUnreal $UNREAL_ENGINE_DIR/Engine/Plugins/Marketplace/\n'

    with open(os.open("%s"%str(self.build_working_dir/"build_obt.sh"), os.O_CREAT | os.O_WRONLY, 0o777), "w") as f:
      f.write(shscr)


    return command.subshell( directory=self.build_working_dir,
                             prompt = "ue5_cesium",
                             environment = dict() )

  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=ue5_cesium.name,
                             repospec="CesiumGS/cesium-unreal",
                             revision="v1.14.0-ue5",
                             shallow=False,
                             recursive=True)

  ########################################################################

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"README.md").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.includes()/"ue5_cesium"/"igl_inline.h").exists()

"""
  560  obt.dep.build.py ue5_cesium --incremental 
  561  cd extern/cesium-native/extern/
  562  ls
  563  cd asyncplusplus/
  564  ls
  565  make
  566  ls -l
  567  vim Makefile 
  568  make clean
  569  mak
  570  make
  571  make clean
  572  VERBOSE=1 make
  573  pwd
  574  ls -l
  575  vim Makefile 
  576  fgrep -R relink *
  577  make pre-install
  578  vim Makefile 
  579  make Async++/preinstall
  580  ls -l
  581  ls CMakeFiles/CMakeRelink.dir/

  .. then for spdlog

"""

"""
ERROR: Failed to copy 
       <STAGING>/.staging-temp/builds/ue5_cesium/extern/cesium-native/extern/KTX-Software/other_lib/mac/Release/SDL2.framework/Versions/Current/Frameworks/hidapi.framework/hidapi 
    to <STAGING>/.staging-temp/builds/packages/CesiumForUnreal/HostProject/Plugins/CesiumForUnreal/extern/cesium-native/extern/KTX-Software/other_lib/mac/Release/SDL2.framework/Versions/Current/Frameworks/hidapi.framework/hidapi

ERROR: Failed to copy <STAGING>/.staging-temp/builds/ue5_cesium/extern/cesium-native/extern/KTX-Software/NOTICE.md to <STAGING>/.staging-temp/builds/packages/CesiumForUnreal/HostProject/Plugins/CesiumForUnreal/extern/cesium-native/extern/KTX-Software/NOTICE.md
       (see /home/michael/Library/Logs/Unreal Engine/LocalBuildLogs/Log.txt for full exception trace)
"""

#dlopen failed: libUnrealEditor-SunPosition.so: cannot open shared object file: No such file or directory

"""
find ../ue5 | grep libUnrealEditor-SunPosition.so
../ue5/Engine/Intermediate/Build/Linux/B4D820EA/UnrealEditor/Development/libUnrealEditor-SunPosition.so_nodebug
../ue5/Engine/Intermediate/Build/Linux/B4D820EA/UnrealEditor/Development/Link-libUnrealEditor-SunPosition.so.link.sh
../ue5/Engine/Intermediate/Build/Linux/B4D820EA/UnrealEditor/Development/libUnrealEditor-SunPosition.so.psym
../ue5/Engine/Plugins/Runtime/SunPosition/Intermediate/Build/Linux/B4D820EA/UnrealEditor/Development/SunPosition/libUnrealEditor-SunPosition.so.response
../ue5/Engine/Plugins/Runtime/SunPosition/Binaries/Linux/libUnrealEditor-SunPosition.so
"""