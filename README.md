# ORK.BUILD TOOLS (OBT)  

### [BuildStatus](https://www.orkid-engine.dev:4431)

* Ubuntu 22.04 [![CISTATUS](https://www.orkid-engine.dev:4431/orkdotbuild-ix-ub2204/develop/status.svg)](https://www.orkid-engine.dev:4431)
* Ubuntu 20.04 [![CISTATUS](https://www.orkid-engine.dev:4431/orkdotbuild-ix-ub2004/develop/status.svg)](https://www.orkid-engine.dev:4431)

### DESCRIPTION  

**ork.build** is a posix (Linux,OSX) *container based* build environment which provides shared functionality for common build automation tasks. **ork.build** also has a set of dependency providers for useful libraries. Unlike homebrew and apt the dependency provider interface is consistent regardless if you are on OSX or Linux - in general the entire interface is consistent on both OSX and Linux. ork.build is implemented primarily in python3. If you need to compose a set of build products with a unified set of versions and configuration data, then ork.build might be for you. It is also important to realize that ork.build is not a replacement for docker style containers. ork.build is specifically a build container environment, as opposed to a machine or microservice container environment. For example, one might use ork.build to prep content for use in a docker container. 

### DEFINITIONS  

* Staging Folder - The container which consists of a top level folder in which all build products go and a set of environment variables
* Module - a python script in OBT or OBT_SEARCH_PATH that describes and implements a subspace, dependency, target and SDK
* Subspace - a subdivision of a staging folder containing build products for a specific target
* Dependency - a recipe for building a package into a subspace, for a target, using an SDK.
* Host - the OS instance that is executing OBT in a shell.
* Target - the OS that code is being generated for (via an SDK)
* SDK - recipes for how to build products for a given target

### USAGE  

**Clone it**
```
git clone https://github.com/tweakoz/ork.build 
```

**Install system scoped dependencies**

```./ork.build/bin/obt.ix.installdeps.ubuntu19.py``` # On Ubuntu 19.04/20.04

Ubuntu may require a few deps to be installed first, like wget, for example..

or

```./ork.build/bin/obt.osx.installdeps.py``` # On MacOs (only MacOs Catalina Intel tested, atm...)

MacOs will require a few deps to be installed first, such as homebrew and macos commandline build tools.

**To create an environment:**

```
ork.build/bin/create_env.py --stagedir <staging_folder>
```

Note that creating a staging environment will build a few core dependencies, such as python and a python virtual environment.

**to launch an environment container:**
*(the container remembers and references the original ork.build folder)*

```
<staging_folder>/.launch_env
```

Launching an environment container will push the launching shell onto the shell process stack, and invoke the modified shell on the next stack level.

**to exit an environment container:**
just exit the shell and you will return to the environment's untouched parent shell.

**to get list of obt commands:** (from bash shell)

we use bash's command line completion and ork.build's convention of prefixing all public commands with *obt*

```
obt.<tab tab>
```

**which returns:** (example)

```
obt.dep.list.py obt.dep.require.py obt.find.py
```

**to get list of obt dependency providers:**

```
obt.dep.list.py
```

**which returns:** (example)


```
     apitrace : ApiTrace (github-master)
   arachnepnr : arachnepnr (git-c40fb2289952f4f120cc10a5a4c82a6fb88442dc)
arm64_binutils : Arm64 BinUtils (source)
    arm64_gcc : Arm64-Gcc
       assimp : assimp (git-obt-v5.0.1)
  astcencoder : ARM ASTC encoder (github-1.7)
    audiofile : audiofile (git-master)
 avr_binutils : Avr BinUtils (source)
      avr_gcc : Avr GCC (source)
     avr_libc : Avr GCC (source)
        blosc : blosc (git-v1.21.1)
        boost : boost (git-boost-1.77.0)
       bullet : bullet (git-2.89)
         calf : CALF (github-master)
         cgal : cgal (git-releases/CGAL-5.0.2)
        clang : Clang(From LLVM)
        cmake : cmake (git-v3.22.1)
       cppzmq : cppzmq (github-v4.7.1)
    csvparser : csvparser (git-master)
         cuda : cuda (system)
       curlpp : curlpp (git-v0.8.1)
       cycles : cycles (git-master)
     drawtext : drawtext (git-v0.5)
     easyprof : easyprof (git-v2.1.0)
        eigen : eigen (git-3.4.0)
       embree : embree (git-v3.9.0)
        faust : faust (github-2.20.2)
     fcollada : fcollada
         fltk : fltk (git-release-1.3.5)
   fluidsynth : CALF (github-v2.1.0)
 frameretrace : FrameRetrace (github)
    gcode_gpr : A simple C++ G-code parser
    gitpython : gitpython (pip3)
         glfw : glfw (git-216d5e8402513b582563d5b8433fefb449a1593e)
          glm : glm (git-master)
       gnutar : gnutar (wget: ftp.gnu.org/gnu/tar/tar-1.34.tar.xz)
      houdini : <houdini.houdini object at 0x7fac5c655c80>
     icestorm : icestorm (git-83b8ef947f77723f602b706eac16281e37de278c)
          igl : igl (git-master)
irix65_binutils : MIPS/IRIX65 BinUtils (source)
   irix65_gcc : irix65 GCC (source)
     irrlicht : irrlicht (homebrew)
         ispc : ispc (wget: https://github.com/ispc/ispc/releases/download/v1.13.0/ispc-v1.13.0-linux.tar.gz)
     ispctexc : ispctexc (git-master)
    jpegturbo : jpegturbo (git-2.1.2)
       lapack : lapack (git-v3.9.0)
   lemongraph : lemongraph (git-master)
    lexertl14 : lexertl14 (git-e9fd6c95b530f3a3840c65e74e79627732cfd4a7)
      libfive : libfive (git-master)
      libpqpp : libpqpp (git-7.4.1)
librealsense2 : librealsense2 (github-v2.42.0)
    libsocket : libsocket (git-master)
     linuxcnc : <linuxcnc.linuxcnc object at 0x7fac5c74b910>
        litex : <litex.litex object at 0x7fac5c6acc30>
         llvm : llvm (git-llvmorg-12.0.1)
lm32_binutils : <lm32_binutils.lm32_binutils object at 0x7fac5c687e60>
     lm32_gcc : <lm32_gcc.lm32_gcc object at 0x7fac5c6d62d0>
          lua : lua (lua.org-source-v5.2.1)
       luajit : LuaJit (luajit.org-source-v2.1)
m68k_amiga_binutils : 68K BinUtils (source)
m68k_amiga_gcc : Amiga-68k-Gcc
     minetest : Minetest (github-commit-03edcafdda550e55e29bf48a682097028ae01306-source)
      nextpnr : nextpnr (git-67bd349e8f38d91a15f54340b29cc77ef156727f)
 nlohmannjson : nlohmannjson (git-v3.6.1)
          nss : nss (git-NSS_3_63_BRANCH)
         nvtt : nvtt (git-toz_orkdotbuild)
         ocio : ocio (git-v2.0.1)
         oiio : oiio (git-release)
       opencv : OpenCV (github-4.1.0)
       opendb : opendb (git-develop)
      openexr : openexr (git-v2.4.1)
     openjpeg : openjpeg (git-v2.4.0)
     openroad : openroad (git-toztest)
   opensubdiv : opensubdiv (git-release)
      openvdb : openvdb (git-v9.0.0)
       openvr : openvr (git-v1.11.11)
  osgeolaszip : osgeolaszip (git-v2.2.0)
  osgeoliblas : osgeoliblas (git-e6a1aaed412d638687b8aec44f7b12df7ca2bbbb)
    osgeoproj : osgeoproj (git-a892e23d9a444e86b35fc67d0fb84e4acca05c2f)
    osgeotiff : osgeotiff (git-3467bd7b49cca8df29efd606a554b5caf910a3d4)
          osl : osl (git-v1.11.16.0)
   parsertl14 : parsertl14 (git-master)
       pillar : pillar-python-sdk (https://github.com/armadillica/pillar)
    pkgconfig : <pkgconfig.pkgconfig object at 0x7fac5c729d70>
   postgresql : Postgresql (10.4-source)
         ptex : ptex (git-v2.4.1)
      pugixml : pugixml (git-v1.11.4)
     pybind11 : pybind11 (git-v2.7.1)
   pydefaults : <pydefaults.pydefaults object at 0x7fac5c5ea780>
     pyopengl : <pyopengl.pyopengl object at 0x7fac5c6bbf50>
        pyqt5 : pyqt5 ()
      pyside2 : <pyside2.pyside2 object at 0x7fac5c6879b0>
       python : Python3 (3.9.4-source)
          qt5 : QT5
        qt5ct : qt5ct (svn-trunk)
 qt5forpython : qt5forpython (git-5.12)
    rapidjson : rapidjson (git-toz-orkid)
         root : <root.root object at 0x7fac5c6bb460>
       rtmidi : rtmidi (git-4.0.0)
rv32_binutils : <rv32_binutils.rv32_binutils object at 0x7fac5c7578c0>
     rv32_gcc : <rv32_gcc.rv32_gcc object at 0x7fac5c6aca50>
       simavr : <simavr.simavr object at 0x7fac5c6bb9b0>
   unittestpp : UnitTestPP (github-master)
          usd : usd (git-release)
       vivado : <vivado.vivado object at 0x7fac5c6e88c0>
          vpf : VPF (github-master)
          vrx : VRX (github-master)
      vst3sdk : VST3SDK (github-master)
       vulkan : Vulkan (lunarg-1.2.170.0)
          wt4 : WT4 (github-4.1.2)
         yarl : YARL (pip3)
        yosys : yosys (git-96b6410dcb7a82e7be8d4a2025835936f2ca84a7)
       zephyr : ZEPHYR (github-tweakoz/litex-edition)
          zmq : zeromq and bindings (github-v4.3.4)
```

**to install a dependency (into the container)** 

eg. boost

```
obt.dep.build.py boost
```

you can force a dep wipe and rebuild like this:

```
obt.dep.build.py boost --force --wipe
```

or an incremntal build (on supported deps).

Incremental dep builds are useful when you are modifying the source of dep - typically for fixing bugs or build issues.

```
obt.dep.build.py boost --incremental
```

**To check the status of a given dep like this**

```obt.dep.status.py oiio``` 

which would return something like 

```
oiio (git-release)
############################################################################################################################
Dependency(RevTopoOrder)   Supported      Manifest    SrcPresent    BinPresent                                    SourceRoot
############################################################################################################################
0. oiio                         True          True          True          True                            ${OBT_BUILDS}/oiio
1. openexr                      True          True          True          True                         ${OBT_BUILDS}/openexr
2. pybind11                     True          True          True          True                        ${OBT_BUILDS}/pybind11
3. fltk                         True          True          True          True                            ${OBT_BUILDS}/fltk
4. cmake                        True          True          True          True                           ${OBT_BUILDS}/cmake
5. jpegturbo                    True          True          True         False                       ${OBT_BUILDS}/jpegturbo
6. pkgconfig                    True          True          True          True                       ${OBT_BUILDS}/pkgconfig
7. root                         True          True          True          True                            ${OBT_BUILDS}/root
8. pydefaults                   True          True          True          True                      ${OBT_BUILDS}/pydefaults
9. python                       True          True          True          True                          ${OBT_BUILDS}/python
```

### HISTORY

**ork.build** historically derives from orkid's old build system, [micro_ork's build system](https://github.com/tweakoz/micro_ork/tree/master/ork.build) in conjunction with concepts from orkid's ['tozkit'](https://github.com/tweakoz/orkid/tree/osl/tozkit) dependency provider system, [homebrew](https://brew.sh/), [apt](https://wiki.debian.org/Apt), and other build systems and package managers I have worked with over the years.

