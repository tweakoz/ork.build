
###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION_MAJOR = "3"
VERSION_MINOR = "14"
VERSION_MICRO = "4"
VERSION = "%s.%s.%s" % (VERSION_MAJOR,VERSION_MINOR,VERSION_MICRO)
HASH = "0c59e606925de30073db6052b0c3a89d"

import os, shutil, tarfile, sys
from obt import dep, host, path, cmake, env, pip, pathtools
from obt.deco import Deco
from obt.wget import wget
from obt.command import Command
from obt import log

deco = Deco()


###############################################################################

class python_from_source(dep.Provider):

  def __init__(self,target=None): ############################################
    super().__init__("python")
    self._debug_build = False
    ##########################################
    if target==None:
      # target implied is host => INIT scope
      self.scope = dep.ProviderScope.INIT
    else:
      assert(False) # not supported yet
    ##########################################
    # TODO - remove recursion...
    #self.declareDep("pkgconfig")
    ##########################################
    # On macOS, openssl + xz are sourced from OBT-built deps instead of
    # /opt/homebrew. The Linux path uses --with-openssl=/usr (system openssl)
    # and the system liblzma, so no declaration needed there.
    ##########################################
    if host.IsOsx:
      self.openssl = self.declareDep("openssl")
      self.xz      = self.declareDep("xz")
    ##########################################
    #print(options)
    build_dest = path.builds()/"python"
    self.build_dest = build_dest
    self.fname = "Python-%s.tgz"%VERSION
    self.source_dir = self.build_dest/("Python-%s"%VERSION)

  ########  

  def __str__(self):
    return "Python3 (%s-source)" % VERSION

  ########

  def env_init(self):
    log.sdk_announce("registering Python(%s) SDK"%VERSION)
    env.set("OBT_PYTHON_SUBSPACE_BUILD_DIR",path.builds())
    env.set("OBT_PYLIB",self.library_dir)
    env.set("OBT_PYPKG",self.site_packages_dir)
    env.set("OBT_PYTHON_HEADER_PATH",self.include_dir)
    env.set("OBT_PYTHON_LIB_PATH",self.home_dir/"lib")
    env.set("OBT_PYTHON_PYLIB_PATH",self.pylib_dir)
    env.set("OBT_PYTHON_LIB_FILE",self.library_file)
    env.set("OBT_PYTHON_LIB_NAME",self.library_name)
    env.set("OBT_PYTHON_DECO_NAME",self._deconame)
    env.set("OBT_PYTHON_DECOD_NAME",self._deconame_d)
    env.set("OBT_PYTHONHOME",self.virtualenv_dir)
    if True: # WIP
      env.prepend("PATH",self.virtualenv_dir/"bin" )
    #env.set("VIRTUAL_ENV",self.virtualenv_dir)
    env.prepend("LD_LIBRARY_PATH",self.home_dir/"lib")
    env.prepend("PKG_CONFIG_PATH",self.library_dir/"pkgconfig")
    # Python was built with --disable-gil (free-threading available).
    # Default the runtime to GIL-on so existing scripts behave as before;
    # users opt in to free-threading per-invocation:
    #   PYTHON_GIL=0 ork.python script.py     # free-threaded (no GIL)
    env.set("PYTHON_GIL","1")

  ########

  def env_goto(self):
    return {
      "pylib": str(self.library_dir),
      "pypkg": str(self.site_packages_dir)
    }

  ########

  def env_properties(self):
    return {
      "pylib": self.library_dir,
      "pypkg": self.site_packages_dir
    }

  ########

  @property
  def version(self):
    va = VERSION_MAJOR
    vb = VERSION_MINOR
    vc = VERSION_MICRO
    return "%s.%s.%s" % (va,vb,vc)
  ########
  @property
  def version_major(self):
    va = VERSION_MAJOR
    vb = VERSION_MINOR
    return "%s.%s" % (va,vb)
  ########
  # Free-threaded CPython (PEP 703) names every artifact with a `t` suffix:
  #   binary:        python3.14t
  #   shared lib:    libpython3.14t.dylib
  #   include dir:   include/python3.14t/
  #   site-packages: lib/python3.14t/site-packages/
  # Configure was invoked with --disable-gil unconditionally (see build()),
  # so deconame must include the `t` to match the on-disk layout. Without
  # this, pydefaults' areRequiredBinaryFilesPresent() looks in
  # lib/python3.14/site-packages/ — which doesn't exist — and the build
  # silently re-runs forever.
  FREE_THREADED = True
  ########
  @property
  def _deconame(self):
    suffix = "t" if self.FREE_THREADED else ""
    return "python%s%s" % (self.version_major, suffix)
  ########
  @property
  def _deconame_d(self):
    a = self._deconame
    if self._debug_build:
      a+= "d"
    return a
  ########
  @property
  def library_dir(self):
    # todo - use pkgconfig ?
    return self.home_dir/"lib"
  ########
  @property
  def venvlibrary_dir(self):
    # todo - use pkgconfig ?
    return self.virtualenv_dir/"lib"
  ########
  @property
  def pylib_dir(self):
    # todo - use pkgconfig ?
    return self.library_dir/self._deconame
  ########
  @property
  def library_file(self):
    # todo - use pkgconfig ?
    return ("lib%s.%s"%(self._deconame_d,self.shlib_extension))
  ########
  @property
  def library_name(self):
    # todo - use pkgconfig ?
    return ("lib%s"%self._deconame_d)
  ########
  @property
  def site_packages_dir(self):
    # todo - use pkgconfig ?
    return self.venvlibrary_dir/self._deconame/"site-packages"
  ########
  @property
  def virtualenv_dir(self):
    return self.home_dir
  ########
  @property
  def home_dir(self):
    return path.Path(os.environ["OBT_PYTHONHOME"])
  ########
  @property
  def include_dir(self):
    return self.home_dir/"include"/self._deconame_d
  ########
  @property
  def numpy_include_dir(self):
    # numpy 2.x moved headers from core/ to _core/
    p = self.site_packages_dir/"numpy"/"_core"/"include"
    if not p.exists():
      p = self.site_packages_dir/"numpy"/"core"/"include"
    return p
  ########
  @property
  def executable(self):
    return self.virtualenv_dir/"bin"/"python3"
  ########

  def download_and_extract(self): #############################################

    url = "https://www.python.org/ftp/python/%s/%s"%(VERSION,self.fname)

    self.arcpath = dep.downloadAndExtract([url],
                                          self.fname,
                                          "gz",
                                          HASH,
                                          self.build_dest)


  def build(self): ############################################################
    # python_from_source extends Provider directly (no builder pattern), so the
    # declared openssl/xz deps don't get auto-required at build time. Force
    # them in explicitly here on macOS. (The previous dep.require("pkgconfig")
    # was removed — Python's configure does not need pkg-config for our build,
    # and removing it kills the brew install pkgconfig path.)
    if host.IsOsx:
      ok = dep.require(["openssl","xz"])
      if not ok:
        return False

    # No os.chdir() anywhere in this method. cwd is process-global and
    # would race under the parallel pipeline (parallel builds for python
    # and e.g. cmake / ffmpeg would clobber each other's cwd, causing
    # "make: *** No rule to make target install" failures).
    # All Command(...) invocations below pass working_dir= explicitly.
    pathtools.ensureDirectoryExists(path.builds())
    self.download_and_extract()
    build_temp = self.source_dir/".build"
    print(build_temp)
    if build_temp.exists():
      shutil.rmtree(str(build_temp), ignore_errors=True)

    build_temp.mkdir(parents=True,exist_ok=True)
    options = [
        "--prefix",self.home_dir,
        #"--enable-loadable-sqlite-extensions",
        "--with-ensurepip=install", # atomically build pip
        # Free-threading (PEP 703): build supports both GIL and no-GIL modes.
        # Defaults to no-GIL when started, but PYTHON_GIL=1 (set in env_init)
        # re-enables the GIL — i.e. by default this stays on the GIL path,
        # opt-in to free-threading via `PYTHON_GIL=0 ork.python script.py`.
        # Note: --enable-experimental-jit is not enabled here because
        # CPython 3.14 forbids combining it with --disable-gil. Re-evaluate
        # for 3.15 where the combination is on the roadmap.
        "--disable-gil",
    ]

    if self._debug_build:
      options += ["--with-pydebug"]

    env.set("CCFLAGS","-march=%s"%self._target.architecture)

    if host.IsOsx:
       from obt import macos
       sdkdir = path.osx_sdkdir()
       print(sdkdir)
       #options += ["--enable-universalsdk=%s"%sdkdir]

       # OBT-built openssl + xz (no homebrew). See modules/dep/openssl.py and xz.py.
       # Both deps install into $OBT_STAGE so we point Python's configure at it.
       options += ["--with-openssl=%s" % self.openssl.root]
       options += ["--with-openssl-rpath=%s" % self.openssl.lib_dir]
       #options += ["--enable-framework"]
       options += ["--enable-shared"]
       # for LZMA — point at OBT-built xz
       env.prepend("LDFLAGS", f"-L{self.xz.lib_dir}")
       env.prepend("CFLAGS",  f"-I{self.xz.include_dir}")
       # disable NLS/libintl - not needed and causes link errors on some systems
       options += ["ac_cv_header_libintl_h=no"]

    else:
       options += ["--with-system-ffi"]
       options += ["--with-openssl=/usr"]
       options += ["--enable-shared"]

    Command(["../configure"]+options, working_dir=build_temp).exec()
    OK = (0==Command(["make",
                      "-j", host.NumCores,
                      "install"], working_dir=build_temp).exec())
    ################################
    # install default packages
    ################################
    if OK:
      env.prepend("LD_LIBRARY_PATH",self.home_dir/"lib")
      obt_python = self.home_dir/"bin"/"python3"
      venv_python = self.virtualenv_dir/"bin"/"python3"
      Command([obt_python,"-m","venv", self.virtualenv_dir],
              working_dir=build_temp).exec()

      modules =  ["yarl","toposort","pytest","os_release","pyyaml", "conan"]

      Command(["cp","../pyvenv/bin/python3.12","python-ork"],
              working_dir=path.stage()/"bin").exec()

    ################################
    return OK

  def areRequiredSourceFilesPresent(self):
    return (self.source_dir/"LICENSE").exists()

  def areRequiredBinaryFilesPresent(self):
    return (self.executable).exists()

  ########################################################################

  def deployment_fixup(self, deploy_root):
    """Fix pyvenv python binary's hardcoded libpython reference to @rpath."""
    import subprocess, glob
    for pybin in glob.glob(f"{deploy_root}/pyvenv/bin/python3.[0-9]*"):
      if os.path.islink(pybin) or pybin.endswith("-config"):
        continue
      otool = subprocess.run(["otool", "-L", pybin], capture_output=True, text=True).stdout
      for line in otool.splitlines()[1:]:
        ref = line.strip().split(" (")[0]
        if "libpython" in ref and not ref.startswith("@rpath"):
          lib = os.path.basename(ref)
          subprocess.run(["install_name_tool", "-change", ref, f"@rpath/{lib}", pybin], capture_output=True)
          for rp in [f"{deploy_root}/pyvenv/lib", f"{deploy_root}/lib"]:
            subprocess.run(["install_name_tool", "-add_rpath", rp, pybin], capture_output=True)
          subprocess.run(["codesign", "--force", "--sign", "-", pybin], capture_output=True)
          break


python = python_from_source

