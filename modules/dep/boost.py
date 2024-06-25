###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION = ["1","81","0"]
HASH = "3276c0637d1be8687740c550237ef999"

import os,tarfile
from obt import path,host,dep, gen_pkgconfig, patch
from obt.wget import wget
from obt.deco import Deco
from obt.command import Command
from pathlib import Path
from yarl import URL

deco = Deco()

###########################################

class boost(dep.Provider):

  ########

  def __init__(self):
    super().__init__("boost")
    self.version = VERSION
    self.baseurl = URL("https://boostorg.jfrog.io/artifactory/main/release")
    self.verurl = self.baseurl/("%s.%s.%s"%(VERSION[0],VERSION[1],VERSION[2]))
    self.fbase = ("boost_%s_%s_%s"%(VERSION[0],VERSION[1],VERSION[2]))
    self.fname = ("%s.tar.bz2"%(self.fbase))
    self.verurl = self.verurl/"source"/self.fname
    build_dest = path.builds()/"boost"
    self.build_dest = build_dest
    self._is_mac_arm = (self._target.identifier == "aarch64-macos")

    SUFFIX = ""
    if self._target.architecture == "x86_64":
      SUFFIX = "x64"
    elif self._target.architecture == "aarch64":
      SUFFIX = "a64"

    self.architecture_suffix = SUFFIX

  ########

  def __str__(self):
    return "Boost ver:%s" % VERSION

  ########

  def wipe(self):
    os.system("rm -rf %s"%self.source_root)

  ########

  def download_and_extract(self):

    self.arcpath = dep.downloadAndExtract([self.verurl],
                                          self.fname,
                                          "bz2",
                                          HASH,
                                          self.build_dest)

  ########

  def build(self):

    PYTHON = dep.instance("python")

    prefix = path.prefix()
    toolset = "darwin" if self._target.os=="macos" else "gcc"

    os.chdir(str(self.build_dest/self.fbase))

    #########################################
    # for MacM1 (ARM)
    #  patch darwin.jam
    #  see https://github.com/boostorg/build/commit/456be0b7ecca065fbccf380c2f51e0985e608ba0.patch?full_index=1
    #  and https://trac.macports.org/ticket/60287
    #########################################

    if toolset == "darwin":
      p = patch.patcher(self)
      p_dest = self.build_dest/self.fbase/"tools"/"build"/"src"/"tools"
      p.patch(p_dest,"darwin.jam")

    #########################################

    cmdlist = [
     "./bootstrap.sh",
     "link=shared",
     "runtime-link=shared",
     "--prefix=%s"%prefix,
     "toolset=%s" % toolset
    ]

    #########################################
    # giving up on boost-python on mac M1 for now...
    #########################################

    if True: #toolset == "darwin":
      cmdlist += ["--without-libraries=python,coroutine"]
    else:
      # broken with python 3.12...
      cmdlist += [
       "--with-python=%s"%PYTHON.executable,
       "--with-python-root=%s"%PYTHON.home_dir,
       "--with-python-version=%s"%(PYTHON.version_major),
    ]

    #########################################

    a = Command(cmdlist).exec()

    OK = (a==0)
    assert(OK)

    #########################################
    # for MacM1 (ARM)
    #  patch project-config.jam
    #  as it cannot correctly find python
    #  see:  https://github.com/boostorg/build/issues/289
    #########################################

    #if self._is_mac_arm:
    #  repl = {
    #    "PY_VER": PYTHON.version_major,
    #    "PY_ROOT": PYTHON.home_dir,
    #    "PY_INC": PYTHON.include_dir,
    #    "PREFIX": path.stage(),
    #  }
    #  p = patch.patcher(self,repl_dict = repl)
    #  p.patch(self.build_dest/self.fbase,"project-config.jam")

    #########################################

    cxxflags = ["-std=c++17","-fPIC"]

    #########################################

    b = Command(["./b2",
                 "--prefix=%s"%prefix,
                 "toolset=%s" % toolset,
                 "link=shared",
                 "runtime-link=shared",
                 "headers"]).exec()

    OK = (b==0)
    assert(OK)

    #########################################

    if host.IsOsx:
      linkflags = ['-Wl,-rpath',str(path.prefix()/"lib")]
      linkflags += ["-stdlib=libc++"]
    else:
      linkflags = ['-Wl,-rpath',str(path.prefix()/"lib")]

    c = Command(["./b2",
                 "--prefix=%s"%prefix,
                 "-d2",
                 "-j%d"%host.NumCores,
                 "-sNO_LZMA=1",
                 "--layout=tagged",
                 "toolset=%s" % toolset,
                 "threading=multi",
                 "address-model=64",
                 'cxxflags=%s' % " ".join(cxxflags),
                 'linkflags=%s' % " ".join(linkflags),
                 "link=shared",
                 "runtime-link=shared",
                 "install"]).exec()

    OK = (c==0)
    assert(OK)

    #########################################

    if OK:
      self.manifest.touch()

    return OK
    #Fixed it by commenting the following in boost/tools/build/src/tools/darwin.jam
    # - GCC 4.0 and higher in Darwin does not have -fcoalesce-templates.
    #if $(real-version) < "4.0.0"
    #{
    #  flags darwin.compile.c++ OPTIONS $(condition) : -fcoalesce-templates ;
    #}

  ###########################################################

  def version(self):
      return "%s.%s.%s"%(VERSION[0],VERSION[1],VERSION[2])

  ###########################################################
  # generate pkgconfig package file
  ###########################################################

  def _generate_pkgconfig(self):
    LIBS_PUBLIC = """
    prg_exec_monitor 
    math_c99f unit_test_framework.
    container log_setup math_tr1l 
    graph wserialization log 
    math_c99f type_erasure signals 
    test_exec_monitor filesystem thread 
    math_tr1f date_time timer 
    math_tr1f test_exec_monitor container 
    math_tr1 type_erasure 
    program_options graph log_setup 
    random system system locale 
    wserialization regex exception 
    timer signals filesystem 
    math_c99 math_tr1 serialization 
    serialization prg_exec_monitor exception 
    coroutine math_c99 iostreams 
    random program_options atomic 
    date_time math_c99l math_tr1l 
    context regex coroutine 
    log chrono wave 
    iostreams chrono unit_test_framework.
    math_c99l
    """.replace("\n","")

    LIBS_PUBLIC = LIBS_PUBLIC.split(" ")
    while("" in LIBS_PUBLIC) :
      LIBS_PUBLIC.remove("")

    SUFFIX = "mt-%s" % self.architecture_suffix

    LIBS_PUBLIC = ["-lboost_%s-%s"%(item,SUFFIX) for item in LIBS_PUBLIC]

    CFLAGS = "-I%s/boost" % path.includes()

    replacements = {
      "NAME": "boost",
      "DESCRIPTION": "OBT boost",
      "VERSION": ("%s.%s.%s"%(VERSION[0],VERSION[1],VERSION[2])),
      "PREFIX": path.stage(),
      "LIBS_PRIVATE":"",
      "LIBS_PUBLIC":"-L%s %s"%(path.libs()," ".join(LIBS_PUBLIC)),
      "CFLAGS":CFLAGS,
    }

    g = gen_pkgconfig.Generator()
    a = g.apply(replacements,outpath=path.pkgconfigdir()/"boost.pc")

    #############################
    # change install names
    #############################

    if self._target.os == "macos":
      print( "MACOS - fixing boost installnames")
      from obt import macos
      libs = [
        "filesystem",
        "system",
        "program_options",
        "thread",
        "chrono",
        "date_time",
        "atomic",
      ]
      for l in libs:
        if self._target.architecture == "aarch64":
          l2 = "libboost_%s-mt-%s.dylib" % (l,self.architecture_suffix)
        else:
          l2 = "libboost_%s-mt-x64.dylib" % (l)
        print(l,l2)
        macos.macho_change_id(path.libs()/l2,"@rpath/%s"%l2)

  ###########################################################

  def cmake_additional_flags(self):
    return {
      "Boost_NO_SYSTEM_PATHS": "ON",
      "BOOST_ROOT": path.stage(),
      #"Boost_DEBUG": "ON",
      "Boost_USE_STATIC_LIBS": "OFF",
      "BOOST_LIBRARYDIR": path.libs(),
      "BOOST_INCLUDEDIR": path.includes(),
      "Boost_ARCHITECTURE": "-%s" % self.architecture_suffix,
    }

  ###########################################################

  def provide(self):
    OK = self.manifest.exists()
    if not self.supports_host:
      print(deco.red("Dependency does not support this host"))
      return False
    ############################
    if self.should_wipe:
      self.wipe()
    ############################
    src_present = self.areRequiredSourceFilesPresent()
    if not src_present:
      self.download_and_extract()
    ############################
    if self.should_build:
      OK = self.build()
    ############################
    self._generate_pkgconfig()

    return OK

  ###########################################################

  def areRequiredSourceFilesPresent(self):
    return (self.build_dest/self.fbase/"boostcpp.jam").exists()

  ###########################################################

  def areRequiredBinaryFilesPresent(self):
    return (path.includes()/"boost"/"blank.hpp").exists()
