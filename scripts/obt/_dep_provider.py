###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, inspect, tarfile, sys
from pathlib import Path
import importlib.util
import obt.path, obt.host
from obt.command import Command, run
from obt.deco import Deco
from obt.wget import wget
from obt import pathtools, cmake, make, path, git, host, subspace
from obt import _dep_impl, _dep_x, _globals, log, buildtrace
from enum import Enum

deco = Deco()

# Deps in this list do NOT auto-declare "root" as a prereq. Originally a
# cycle-break for the python/pydefaults/openssl/xz bootstrap chain (per
# NOHOMEBREW.md). cmake is added because it's a self-contained bootstrap
# (system C++ compiler, --system-zlib, no openssl) that needs nothing
# from the rest of the bootstrap chain — letting it run in parallel with
# python saves ~3 min on a clean staging.
# moltenvk is added for the same reason: its build is xcodebuild +
# ./fetchDependencies + system git/curl/wget — it needs nothing from the
# python bootstrap. Without this it would auto-declare root (→ pydefaults
# → python) and serialize behind the whole bootstrap; with it, MoltenVK's
# long xcodebuild overlaps cmake + python.
# pybind11 is here so it builds immediately after python+cmake — in
# parallel with the rest of the bootstrap — instead of waiting on
# pydefaults via the implicit root edge. It's a frequent prereq (pytorch,
# opencv, pangolin, ...) carrying build_priority=100, so clearing it early
# unblocks the long-pole chain. pybind11 still explicitly declares its
# real prereqs (python, cmake). NOTE: `root` does NOT declare pybind11 —
# that was tried and reverted (it serialized vulkan etc behind pybind11).
root_dep_list = ["root", "python", "pydefaults", "openssl", "xz", "cmake", "moltenvk", "pybind11"]

class ProviderScope(Enum):
  CONTAINER = 1 # dependency is scoped to the container
  INIT = 2  # dependency is scoped to the container and rendered upon creation of container (always present)
  HOST = 3 # dependency is sourced from the host (apt install, brew install, etc...)
  SUBSPACE = 4 # dependency is scoped to the subspace

###############################################################################
class Provider(object):
    """base class for all dependency providers"""
    def __init__(self,name,target=None,subspace_vif=1):
      self._subspace_vif = subspace_vif
      self.scope = ProviderScope.CONTAINER
      self._allow_build_in_subspaces = False 
      if target ==None:
        self._target = host.description().target
      else:
        self._target = target
      self._name = name
      self._miscoptions = _globals.getOptions()
      self._node = None
      self._deps = {}
      self._archlist = None 
      self._oslist = None 
      self._src_required_files = []
      self._bin_required_files = []
      self._required_deps = {}
      self._topoindex = -1
      self._debug = False
      self._must_build_in_tree = False
      # Per-dep escape hatches for the parallel pipeline scheduler.
      # When True, the scheduler drains the corresponding pool and runs this
      # dep alone in that stage. The other stage's pool is unaffected.
      # Default False; deps with known concurrency hazards opt in.
      self.serial_fetch = False
      self.serial_build = False
      # Build-dispatch priority for the parallel pipeline. When more deps
      # are eligible than there are free build slots, the scheduler
      # dispatches highest build_priority first (ties broken by topo
      # order). Use it to front-load long-pole deps (e.g. pytorch) so a
      # slow serial build starts in the first wave instead of queueing.
      # Default 0; higher = sooner.
      self.build_priority = 0
      if name not in root_dep_list:
        self.declareDep("root")
      #############################
      self.setSourceRoot(path.builds()/name)
      if subspace_vif==2:
        #self.setSourceRoot(path.subspace_builds()/name)
        self._allow_build_in_subspaces = True
      #############################
    #############################
    @property
    def manifest_dir(self):
      subspace_path = path.subspace_dir()/"manifests"
      stage_path = path.stage()/"manifests"
      is_host = subspace.is_host_subspace()
      is_host = is_host or (self.scope!=ProviderScope.SUBSPACE)
      return stage_path if is_host else subspace_path 
    #############################
    @property
    def manifest(self):
      return self.manifest_dir / self._name 
    #############################
    @property
    def OK(self):
      return self.manifest.exists()
    #############################
    def declareDep(self, named):
      inst = _dep_x.instance(named)
      #print(named,type(inst))
      self._required_deps[named] = inst
      return inst
    #############################
    def declareDeps(self, list_of_deps):
      list_of_insts = []
      for named in list_of_deps:
        inst = _dep_x.instance(named)
        #print(named,type(inst))
        self._required_deps[named] = inst
        list_of_insts.append(inst)
      return list_of_insts
    #############################
    def createBuilder(self,clazz, **kwargs):

      if len(kwargs)>0:
        self._builder = clazz(self._name,**kwargs)
      else:
        self._builder = clazz(self._name)
      if len(self._required_deps):
        self._builder.requires(self._required_deps)
      return self._builder
    #############################
    def setSourceRoot(self,srcroot):
      self.source_root = srcroot
      self.build_src = srcroot
      self.build_dest = srcroot/".build"
      self.build_working_dir = self.build_dest
    #############################
    def mustBuildInTree(self):
      self.build_dest = self.build_src
      self._must_build_in_tree = True
    #########################################
    def areRequiredSourceFilesPresent(self):
      return None
    #########################################
    def areRequiredBinaryFilesPresent(self):
      return self.areRequiredSourceFilesPresent()
    #############################
    @property
    def scopestr(self):
      return str(self.scope).split('.')[1]
    #############################
    ## wipe build ?
    #############################
    @property
    def supports_host(self):
      """predicate determining if dependency supports the host architecture and OS"""
      supports = False 
      #####################################
      def check_os():
        check = False
        if self._oslist==None:
          check = True
        elif host.IsDarwin and ("Darwin" in self._oslist):
          check = True
        elif host.IsLinux and ("Linux" in self._oslist):
          check = True
        elif host.IsIrix and ("IRIX64" in self._oslist):
          check = True
        return check
      #####################################
      def check_arch():
        check = False
        if self._archlist==None:
          check = True
        elif host.IsX86_64 and ("x86_64" in self._archlist):
          check = True
        elif host.IsAARCH64 and ("aarch64" in self._archlist):
          check = True
        return check
      #####################################
      return check_os() and check_arch()

    #############################
    ## Is this the primary dep provvider?
    #############################
    @property
    def is_primary_dep(self):
      if "depname" in self._miscoptions:
        if self._name == self._miscoptions["depname"]:
          return True 
      return False  
    #############################
    ## wipe build ?
    #############################

    @property
    def should_wipe(self):
      """predicate controlling build-clean during provisioning of a dependency"""
      wipe = False
      if "wipe" in self._miscoptions:
        wipe = self._miscoptions["wipe"]==True
      return wipe and self.is_primary_dep

    #############################
    ## serial build ?
    #############################

    @property
    def should_serial_build(self):
      """predicate controlling 1cpu build during provisioning of a dependency (for build debugging)"""
      serial = False
      if "serial" in self._miscoptions:
        serial = self._miscoptions["serial"]==True
      return serial

    @property
    def default_parallelism(self):
      parallelism = 1.0
      if self.should_serial_build:
        parallelism=0.0
      return parallelism

    #############################
    ## force build ?
    #############################

    @property
    def should_force_build(self):
        force = False
        if "force" in self._miscoptions:
          force = self._miscoptions["force"]==True
        return force and self.is_primary_dep

    #############################
    ## force build ?
    #############################

    @property
    def should_incremental_build(self):
        incremental = False
        if "incremental" in self._miscoptions:
          incremental = self._miscoptions["incremental"]==True
        return incremental and self.is_primary_dep

    #############################

    @property
    def should_build(self):
      # should_wipe implies rebuild: callers (obt.dep.build.py, the pipeline)
      # gate provide() on should_build, so a wipe that doesn't set it is a
      # silent no-op that exits 0 — a lying success.
      needs = (not self.manifest.exists()) or self.should_force_build \
              or self.should_incremental_build or self.should_wipe
      if subspace.targeting_host():
        return needs
      else:
        if self._allow_build_in_subspaces:
          if self._subspace_vif==2:
            return needs
        return False
      
    #############################

    @property
    def should_fetch(self):
        fetch = False
        if "nofetch" in self._miscoptions:
          fetch = self._miscoptions["nofetch"]==False
        return fetch

    #############################

    @property
    def _std_cmake_vars():
      cmakeEnv = {
        "CMAKE_BUILD_TYPE": "Release",
        "BUILD_SHARED_LIBS": "ON",
      }
      return cmakeEnv

    #############################

    @property
    def exists(self):
        return False

    #############################

    def option(self,named):
      if named in self._miscoptions:
        return self._miscoptions[named]
      else:
        return None

    #############################

    def _old_provide(self): 
      OK = True
      if not self.manifest.exists():
        OK = False
      if not OK:
        if hasattr(self,"download_and_extract"):
          self.download_and_extract()
        OK = self.build()
        if OK:
          self.manifest.touch()
      return OK

    #############################

    def provide(self):
      import obt.path
      if obt.path.has_deployment_marker:
        return True
      if not self.supports_host:
        print(deco.red("Dependency does not support this host"))
        return False
      if self.should_wipe:
        self.wipe()
      OK = True
      if self.should_build:
        with buildtrace.NestedBuildTrace({ "op": "Provider.provide(%s)"%self._name }) as nested:
          OK = self.build()
          if OK:
            OK = self.onPostBuild()
            if OK:
              bins_present=self.areRequiredBinaryFilesPresent()
              if bins_present != None:
                OK = bins_present
              else:
                OK = True
              if OK:
                self.manifest.touch()
      return OK


    #############################

    def onPostBuild(self):
      return True

    #############################
    def onPostInstall(self):
      return True

    #############################
    # Default fetch/build split for non-StdProvider subclasses (e.g.
    # HomebrewProvider). These don't have a separable fetch stage, so
    # fetch_only is a no-op and build_and_install delegates to provide().
    # StdProvider overrides both with real implementations.
    #############################
    def fetch_only(self):
      return True

    #############################
    def build_and_install(self):
      return self.provide()

    #############################

    def _std_cmake_build(self,srcdir,blddir,cmakeEnv=_std_cmake_vars,parallelism=1.0):
      ok2build = True
      if self.should_incremental_build:
        os.chdir(blddir)
      else:
        pathtools.mkdir(blddir,clean=True)
        pathtools.chdir(blddir)
        cmake_ctx = cmake.context(root=srcdir,env=cmakeEnv)
        ok2build = cmake_ctx.exec()==0
      if ok2build:
        return (make.exec("install",parallelism=parallelism)==0)
      return False

    #############################

    def wipe(self):
        pass

    #############################

    def node(self):
        return self._node

    #############################

    @property
    def shlib_extension(self):
      if host.IsOsx:
        return "dylib"
      if host.IsIx:
        return "so"

###############################################################################

class HomebrewProvider(Provider):
  def __init__(self,name,pkgname):
    super().__init__(pkgname)
    self.pkgname = pkgname
    self._deps = list()
  ###########################################
  def requires(self,deplist):
    self._deps += deplist
  ###########################################
  def brew_prefix(self):
    return Path("/")/"usr"/"local"
  ###########################################
  def build(self):
    for item in self._deps:
      n = _dep_x.instance(item)
      #print(item,n)
      assert(n!=None)
      n.provide()
    retc = Command(["brew","install",self.pkgname]).exec()
    if 0 == retc:
      self.manifest.touch()
    return 0==retc

###############################################################################

class StdProvider(Provider):
    #############################
    def __init__(self,name,subspace_vif=1):
      super().__init__(name,subspace_vif=subspace_vif)
      self._builder = None

    ########

    @property
    def _fetcher(self):
      return None

    #############################
    def postinit(self):
      pass
    #############################
    def requires(self,deplist):
      self._builder.requires(deplist)
    #############################
    def install(self):
      return self._builder.install(self.build_dest)
    #############################
    def __str__(self):
      if hasattr(self,"descriptor"):
        return self.descriptor()
      else:
        return self._fetcher.descriptor()
    #############################
    def wipe(self):
      os.system("rm -rf %s"%self.source_root)
    #############################
    def updateSource(self):
        return self._fetcher.update(self.source_root)
    #############################
    def _fetch(self):
      source_exists = self.areRequiredSourceFilesPresent()
      #print(deco.bright("STDPROVIDER<%s> source_exists<%s>"%(self._name,source_exists)))
      fetchOK = False
      if not source_exists:
        print(deco.bright("Fetching<%s>"%(self._name)))
        fetchOK = self._fetcher.fetch(self.source_root)
        #assert(fetchOK==True or fetchOK==False)
        if fetchOK:
          self._fetcher.patch()
        else:
          print(deco.err("Fetch <%s> failed!"%self._name))
          fetchOK = False
      return fetchOK 
    #############################
    def build(self):
      if self.areRequiredSourceFilesPresent() == False:
        print(deco.red("Cannot build <%s> missing files[%s]"%(self._name,self._src_required_files)))
        return False
      #########################################
      # build
      #########################################
      print(deco.bright("Building<%s>"%(self._name)))
      OK = self._builder.build(self.build_src,
                                    self.build_dest,
                                    self.build_working_dir,
                                    self.should_incremental_build)
      #########################################
      if not OK:
        print(deco.err("Build <%s> failed!"%self._name))
      return OK
    #########################################
    def install(self):
      return self._builder.install(self.build_dest)
    #########################################
    def fetch_only(self):
      """Fetch source for this dep. Does NOT build or install.
      Returns True if source is ready (already cached or freshly fetched),
      False on terminal fetch failure. Safe to call from the parallel
      pipeline's fetch pool."""
      import obt.path
      if obt.path.has_deployment_marker:
        return True
      with buildtrace.NestedBuildTrace({ "op": "StdProvider.fetch_only(%s)"%self._name }) as nested:
        self.postinit()
        if self.should_wipe:
          self.wipe()
        if self.areRequiredSourceFilesPresent():
          return True
        fetch_ok = self._fetch()
        if not fetch_ok:
          print(deco.err("Fetch <%s> failed!"%self._name))
          return False
        return True
    #########################################
    def build_and_install(self):
      """Build, post-build, install, post-install, and write manifest.
      Assumes source has already been fetched (call fetch_only() first or
      let provide() chain them). Returns True on success.

      Honors the manifest short-circuit: if the manifest exists and
      should_build is False, returns True without doing work."""
      import obt.path
      if obt.path.has_deployment_marker:
        return True
      with buildtrace.NestedBuildTrace({ "op": "StdProvider.build_and_install(%s)"%self._name }) as nested:
        OK = self.manifest.exists()
        if self.should_build:
          OK = self.build()
          if OK:
            OK = self.onPostBuild()
            if OK:
              OK = self.install()
              if OK:
                OK = self.onPostInstall()
              else:
                print(deco.err("Install <%s> failed!"%self._name))
            else:
              return False
        if OK:
          self.manifest.touch()
        return OK
    #########################################
    def provide(self):
      """Back-compat: fetch + build + install in one call. The serial
      `obt.dep.build.py` path uses this. The parallel pipeline calls
      fetch_only() and build_and_install() separately so the two stages
      can overlap across deps."""
      if not self.fetch_only():
        return False
      return self.build_and_install()
    #########################################

