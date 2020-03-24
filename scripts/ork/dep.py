###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, inspect, tarfile
from pathlib import Path
import importlib.util
import ork.path
from ork.command import Command
from ork.deco import Deco
from ork.wget import wget
from ork import pathtools, cmake, make, path, git

deco = Deco()

global global_options
global_options =[]

###############################################################################

def _get_instance(item):
  if(isinstance(item,str)):
    node = DepNode(item)
    return node.instance
  elif (isinstance(item,DepNode)):
    return item.instance
  elif (isinstance(item,Provider)):
    return item
  else:
    assert(False)

###############################################################################

def _get_node(item):
  if(isinstance(item,str)):
    node = DepNode(item)
    return node
  elif (isinstance(item,DepNode)):
    return item
  else:
    assert(False)

###############################################################################

def instance(name):
  return _get_instance(name)

###############################################################################

def require(name_or_list):
  if (isinstance(name_or_list,list)):
    rval = []
    for item in name_or_list:
      inst = _get_instance(item)
      inst.provide()
      rval += [inst]
  else:
    inst = _get_instance(name_or_list)
    ok = inst.provide()
    if ok:
      rval = inst
    else:
      rval = None
  return rval


###############################################################################

class Provider(object):
    """base class for all dependency providers"""
    def __init__(self):
      self._miscoptions = global_options
      self._node = None
      self._deps = {}
    #############################

    def option(self,named):
      if named in self._miscoptions:
        return self._miscoptions[named]
      else:
        return None

    #############################
    ## wipe build ?
    #############################

    def should_wipe(self):
        wipe = False
        if "wipe" in self._miscoptions:
          wipe = self._miscoptions["wipe"]==True
        return wipe

    #############################
    ## serial build ?
    #############################

    def should_serial_build(self):
        serial = False
        if "serial" in self._miscoptions:
          serial = self._miscoptions["serial"]==True
        return serial

    def default_parallelism(self):
      parallelism = 1.0
      if self.should_serial_build():
        parallelism=0.0
      return parallelism

    #############################
    ## force build ?
    #############################

    def force(self):
        force = False
        if "force" in self._miscoptions:
          force = self._miscoptions["force"]==True
        return force

    #############################
    ## force build ?
    #############################

    def incremental(self):
        incremental = False
        if "incremental" in self._miscoptions:
          incremental = self._miscoptions["incremental"]==True
        return incremental

    #############################

    def should_build(self):
        no_manifest = (False==self.manifest.exists())
        force = self.force()
        incremental = self.incremental()
        return no_manifest or force or incremental

    #############################

    def should_fetch(self):
        fetch = False
        if "nofetch" in self._miscoptions:
          fetch = self._miscoptions["nofetch"]==False
        return fetch

    #############################

    def provide(self):
      if self.should_wipe():
        self.wipe()
      if self.should_build():
        self.OK = self.build()
      if self.OK:
        self.manifest.touch()
      return self.OK

    #############################

    def _std_cmake_vars():
      cmakeEnv = {
        "CMAKE_BUILD_TYPE": "Release",
        "BUILD_SHARED_LIBS": "ON",
      }
      return cmakeEnv

    #############################

    def _std_cmake_build(self,srcdir,blddir,cmakeEnv=_std_cmake_vars(),parallelism=1.0):
      ok2build = True
      if self.incremental():
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

    def exists(self):
        return False

###############################################################################

def enumerate():
  deps = ork.pathtools.patglob(ork.path.deps(),"*.py")
  depnames = set()
  depnodes = dict()
  for item in deps:
    d = os.path.basename(item)
    d = os.path.splitext(d)[0]
    depnames.add(d)
    #print(d)
    dn = ork.dep.DepNode(d)
    if dn:
        depnodes[d] = dn
  return depnodes

###############################################################################

def enumerate_with_method(named):
  depnodes = enumerate()
  rval = {}
  for depitemk in depnodes:
    depitem = depnodes[depitemk]
    if hasattr(depitem,"instance"):
      if hasattr(depitem.instance,named):
        rval[depitemk] = depitem.instance
  return rval

###############################################################################

class GitFetcher:
  ###########################################
  def __init__(self,name):
    self._name = name
    self._git_url = ""
    self._revision = ""
    self._recursive = False
    self._cache = True
  ###########################################
  def descriptor(self):
    return "%s (git-%s)" % (self._name,self._revision)
  ###########################################
  def fetch(self,dest):
    git.Clone(self._git_url,dest,self._revision,recursive=self._recursive,cache=self._cache)
  ###########################################

###############################################################################

class WgetFetcher:
  ###########################################
  def __init__(self,name):
    self._name = name
    self._fname = ""
    self._url = ""
    self._md5 = ""
    self._arcpath = ""
    self._arctype = ""
  ###########################################
  def descriptor(self):
    return "%s (wget: %s)" % (self._name,self._url)
  ###########################################
  def fetch(self,dest):
    from yarl import URL
    url = URL(self._url)
    dest = path.builds()/self._name
    self._arcpath = downloadAndExtract([url],
                                       self._fname,
                                       self._arctype,
                                       self._md5,
                                       dest)
    return self._arcpath!=None
  ###########################################

###############################################################################

class NopFetcher:
  ###########################################
  def __init__(self,name):
    self._name = name
    self._revision = ""
  ###########################################
  def descriptor(self):
    return "%s (%s)" % (self._name,self._revision)
  ###########################################
  def fetch(self,dest):
    pass
  ###########################################

###############################################################################
class InstallerItem:
  def __init__(self,src,dst):
    self._src = src
    self._dst = dst
class BinInstaller:
  def __init__(self,name):
    self._deps = []
    self._items = []
    self._name = name
    self._OK = True
  ###########################################
  def requires(self,deplist):
    self._deps += deplist
  ###########################################
  def build(self,srcdir,blddir,incremental=False):
    require(self._deps)
    for item in self._items:
      exists = item._src.exists()
      print(item,item._src,exists)
      if False==exists:
        self._OK = False
        return False
    return True
  ###########################################
  def declare(self,src,dst):
    self._items += [InstallerItem(src,dst)]
  ###########################################
  def install(self,blddir):
    for item in self._items:
      cmd = [
        "cp", str(item._src), str(item._dst)
      ]
      Command(cmd).exec()
    return self._OK
  ###########################################

###############################################################################

class CMakeBuilder:
  ###########################################
  def __init__(self,name):
    ##################################
    # ensure environment cmake present
    ##################################
    ##################################
    self._name = name
    self._cmakeenv = {
      "CMAKE_BUILD_TYPE": "Release",
      "BUILD_SHARED_LIBS": "ON",
    }
    self._parallelism=1.0
    self._deps = []
    if name!="cmake":
      self._deps += ["cmake"]
  ###########################################
  def requires(self,deplist):
    self._deps += deplist
  ###########################################
  def setCmVar(self,key,value):
    self._cmakeenv[key] = value
  ###########################################
  def setCmVars(self,othdict):
    for k in othdict:
      self._cmakeenv[k] = othdict[k]
  ###########################################
  def build(self,srcdir,blddir,incremental=False):
    require(self._deps)
    ok2build = True
    if incremental:
      os.chdir(blddir)
    else:
      pathtools.mkdir(blddir,clean=True)
      pathtools.chdir(blddir)
      cmake_ctx = cmake.context(root=srcdir,env=self._cmakeenv)
      ok2build = cmake_ctx.exec()==0
    if ok2build:
      return (make.exec(parallelism=self._parallelism)==0)
    return False
  ###########################################
  def install(self,blddir):
    pathtools.chdir(blddir)
    return (make.exec("install",parallelism=0.0)==0)
  ###########################################

###############################################################################

class StdProvider(Provider):

    #############################

    def __init__(self,name):
      super().__init__()
      self._fetcher = None
      self._builder = None
      self._node = None
      self.manifest = path.manifests()/name
      self.OK = self.manifest.exists()
      self.source_root = path.builds()/name
      self.build_src = self.source_root
      self.build_dest = self.source_root/".build"

    #############################

    def postinit(self):
      print(self._deps)

    #############################

    def install(self):
      return self._builder.install(self.build_dest)

    #############################

    def __str__(self):
      return self._fetcher.descriptor()

    #############################

    def wipe(self):
      os.system("rm -rf %s"%self.source_root)

    #############################

    def build(self):

      #########################################
      # fetch source
      #########################################

      if not self.source_root.exists():
        fetchOK = self._fetcher.fetch(self.source_root)
        if False==fetchOK:
          self.OK = False
          return False

      #########################################
      # build
      #########################################

      self.OK = self._builder.build(self.build_src,self.build_dest,self.incremental())

      #########################################
      return self.OK

    #########################################

    def provide(self):
      self.postinit()
      if self.should_wipe():
        self.wipe()
      if self.should_build():
        self.OK = self.build()
        if self.OK:
          self.OK = self.install()
      if self.OK:
        self.manifest.touch()
      return self.OK

###############################################################################

class DepNode:
    """dependency provider node"""
    def __init__(self,name=None):
      assert(isinstance(name,str))
      self.miscoptions = global_options
      self.name = name
      self.scrname = ("%s.py"%name)
      self.module_path = ork.path.deps()/self.scrname
      self.module_spec = importlib.util.spec_from_file_location(self.name, str(self.module_path))
      self.module = importlib.util.module_from_spec(self.module_spec)
      #print(name,dir(self.module))
      self.module_spec.loader.exec_module(self.module)
      if(hasattr(self.module,name)):
        assert(hasattr(self.module,name))
        self.module_class = getattr(self.module,name)
        assert(inspect.isclass(self.module_class))
        assert(issubclass(self.module_class,Provider))
        self.instance = self.module_class()
        self.instance._node = self

    ## string descriptor of dependency

    def __str__(self):
      return str(self.instance) if hasattr(self,"instance") else "???"

    ## provider method

    def provide(self):
      #print(self.instance)
      if self.instance.exists():
        provide = self.instance.provide()
        assert(provide==True)
        return provide
      else:
        provide = self.instance.provide()
        assert(provide==True)
        return provide

###############################################################################

def downloadAndExtract(urls,
                       outname,
                       archive_type,
                       md5val,
                       build_dest):

  arcpath = wget( urls = urls,
                  output_name = outname,
                  md5val = md5val )


  if arcpath:
    if build_dest.exists():
      Command(["rm","-rf",build_dest]).exec()
    print("extracting<%s> to build_dest<%s>"%(deco.path(arcpath),deco.path(build_dest)))
    print(archive_type)
    build_dest.mkdir()
    if( archive_type=="zip" ):
        os.chdir(str(build_dest))
        Command(["unzip",arcpath]).exec()
    elif archive_type=="tgz":
        os.chdir(str(build_dest))
        Command(["tar","xvfz",arcpath]).exec()
    else:
        assert(tarfile.is_tarfile(str(arcpath)))
        tf = tarfile.open(str(arcpath),mode='r:%s'%archive_type)
        tf.extractall(path=str(build_dest))

  return arcpath

###############################################################################
