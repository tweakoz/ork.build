#!/usr/bin/env python3
###############################################################################
# Orkid Build System
# Copyright 2010-2023, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, sys, argparse, inspect, pathlib, subprocess, multiprocessing, json, importlib
Path = pathlib.Path

from obt.deco import Deco 

deco = Deco()
###########################################

def env_is_set(key):
  return str(key) in os.environ and os.environ[str(key)]!=None

def _genpath(inp):
  return pathlib.Path(os.path.realpath(str(inp)))

def _genpaths(inp):
  p = inp.split(":")
  p = [_genpath(x) for x in p]
  # return unique paths, preserving order 
  uset = set()
  rval = []
  for x in p:
    if x not in uset:
      uset.add(x)
      rval.append(x)
  return rval

def _pathlist_to_str(inp):
  as_str = ""
  count = len(inp)
  uset = set()
  for i in range(count):
    item = inp[i]
    item_str = str(item)
    if item_str not in uset:
      if i!=0:
        as_str += ":"
      as_str += item_str
  return as_str

###########################################
# need private copy of InvokingModule fns
###########################################

def _fileOfInvokingModule():
  frame = inspect.stack()[1]
  module = inspect.getmodule(frame[0])
  if module:
    return _genpath(module.__file__)
  else:
      assert(False)

def _directoryOfInvokingModule():
  frame = inspect.stack()[1]
  module = inspect.getmodule(frame[0])
  if module:
    return _genpath(os.path.dirname(module.__file__))
  else:
      assert(False)

###########################################

def _ppath(p):
  return str(p)

def _listToStrList(l):
  return [str(x) for x in l]

def _ppaths(plist):
  rval = ""
  for p in plist:
    rval += "\n\t"+_ppath(p)
  rval += "\n"
  return rval

def findExecutable(exec_name):
  for path_dir in os.environ["PATH"].split(os.pathsep):
    exec_path = os.path.join(path_dir, exec_name)
    if os.path.isfile(exec_path) and os.access(exec_path, os.X_OK):
      return _genpath(exec_path)
  return None

###########################################

def importProject(config):

  try_project_manifest = config.project_dir/"obt.project"/"obt.manifest"

  if try_project_manifest.exists():
    manifest_json = json.load(open(try_project_manifest,"r"))
    #print(manifest_json)
    config._project_name = manifest_json["name"]
    autoexec = manifest_json["autoexec"]
    autoexec = config.project_dir/"obt.project"/autoexec
    #print(autoexec)
    assert(autoexec.exists())
    # import autoexec as python module
    spec = importlib.util.spec_from_file_location("autoexec", str(autoexec))
    init_env = importlib.util.module_from_spec(spec) 
    spec.loader.exec_module(init_env)
    init_env.setup()


###########################################
# Global OBT process execution configuration
#
#  These may be intialized from a couple different paths:
#
#  1. (EXPLICIT) from an OBT script which is run outside of an OBT environment
#       eg obt.env.launch.py, obt.env.create.py
#       in this case the config is initialized from command line arguments
#  2. (IMPLICIT) from OBT scripts running from within an OBT environment
#       eg obt.dep.list.py 
#       in this case
#
#########
#
#  All OBT core path setup should be controlled ONLY by this config
#   and used elsewhere in the OBT codebase. or external OBT based projects
#  Theory of opertation:
#   1. Place all top level configuration into environment
#      variables as early as possible.
#   2. keep state which can be derived soley from env vars as such..
#   3. stack or subspace operations can inherit and modify from upper OBT stack level env vars
#
# ###########################################

###########################################
# The location of this config module is in bin_pub because it needs to be available:
#   1. from outside of an OBT environment 
#   2. AND early in script startup (before sys.paths are setup)
# This also implies this config object cannot import OBT modules itself (self contained)
###########################################

class ObtExecConfig(object):

  #####################################################################

  def __init__(self): # default initialization from env vars

    self._command = None
    self._disable_syspypath = True
    self._git_ssh_command = None

  #####################################################################
  @property 
  def num_cores(self):
    return os.environ["OBT_NUM_CORES"]
  #####################################################################
  @property 
  def inplace(self):
    return env_is_set("OBT_INPLACE")
  #####################################################################
  @property 
  def quiet(self):
    return env_is_set("OBT_QUIET")
  #####################################################################
  @property 
  def subspace(self):
    if env_is_set("OBT_SUBSPACE"):
      return os.environ["OBT_SUBSPACE"]
    else:
      return None
  #####################################################################
  @property 
  def subspace_dir(self):
    if env_is_set("OBT_SUBSPACE_DIR"):
      return _genpath(os.environ["OBT_SUBSPACE_DIR"])
    else:
      return None
  #####################################################################
  @property 
  def subspace_bin_dir(self):
    return self.subspace_dir/"bin"
  #####################################################################
  @property 
  def subspace_lib_dir(self):
    return self.subspace_dir/"lib"
  #####################################################################
  @property 
  def subspace_build_dir(self):
    return self.subspace_dir/"builds"
  #####################################################################
  @property 
  def subspace_is_conda(self):
    return "conda" in os.environ["OBT_SUBSPACE_DIR"]
  #####################################################################
  @property 
  def text_search_exts(self):
    return os.environ["OBT_SEARCH_EXTLIST"].split(":")
  #####################################################################
  @property 
  def text_search_path(self):
    if env_is_set("OBT_SEARCH_PATH"):
      return _genpaths(os.environ["OBT_SEARCH_PATH"])
    else:
      return []
  #####################################################################
  @property 
  def project_name(self):
    return os.environ["OBT_PROJECT_NAME"]
  #####################################################################
  @property 
  def root_dir(self):
    if env_is_set("OBT_ROOT"):
      return _genpath(os.environ["OBT_ROOT"])
    else:
      return None
  #####################################################################
  @property 
  def scripts_dir(self):
    if env_is_set("OBT_SCRIPTS_DIR"):
      return _genpath(os.environ["OBT_SCRIPTS_DIR"])
    else:
      return None
  #####################################################################
  @property 
  def stage_dir(self):
    if env_is_set("OBT_STAGE"):
      return _genpath(os.environ["OBT_STAGE"])
    else:
      return None
  #####################################################################
  @property 
  def project_dir(self):
    if env_is_set("OBT_PROJECT_DIR"):
      return _genpath(os.environ["OBT_PROJECT_DIR"])
    else:
      return None
  #####################################################################
  @property 
  def build_dir(self):
    return self.stage_dir/"builds"
  #####################################################################
  @property 
  def original_python_path(self):
    if env_is_set("OBT_ORIGINAL_PYTHONPATH"):
      return _genpaths(os.environ["OBT_ORIGINAL_PYTHONPATH"])
    else:
      return []
  #####################################################################
  @property 
  def python_home(self):
    if env_is_set("OBT_PYTHONHOME"):
      return _genpath(os.environ["OBT_PYTHONHOME"])
    else:
      return None
  #####################################################################
  @property 
  def python_path(self):
    if env_is_set("PYTHONPATH"):
      return _genpaths(os.environ["PYTHONPATH"])
    else:
      return []
  #####################################################################
  @property 
  def original_ld_library_path(self):
    if env_is_set("OBT_ORIGINAL_LD_LIBRARY_PATH"):
      return _genpaths(os.environ["OBT_ORIGINAL_LD_LIBRARY_PATH"])
    else:
      return []
  #####################################################################
  @property 
  def original_pkg_path(self):
    if env_is_set("OBT_ORIGINAL_PKG_CONFIG_PATH"):
      return _genpaths(os.environ["OBT_ORIGINAL_PKG_CONFIG_PATH"])
    else:
      return []
  #####################################################################
  @property 
  def modules_path(self):
    if env_is_set("OBT_MODULES_PATH"):
      return _genpaths(os.environ["OBT_MODULES_PATH"])
    else:
      return []
  #####################################################################
  @property 
  def dep_path(self):
    if env_is_set("OBT_DEP_PATH"):
      return _genpaths(os.environ["OBT_DEP_PATH"])
    else:
      return []
  #####################################################################
  @property 
  def bin_pub_dir(self):
    if env_is_set("OBT_BIN_PUB_DIR"):
      return _genpath(os.environ["OBT_BIN_PUB_DIR"])
    else:
      return None
  #####################################################################
  @property 
  def bin_priv_dir(self):
    if env_is_set("OBT_BIN_PRIV_DIR"):
      return _genpath(os.environ["OBT_BIN_PRIV_DIR"])
    else:
      return None
  #####################################################################
  @property 
  def python_package_install_dir(self):
    if env_is_set("OBT_PYPKG"):
      return _genpath(os.environ["OBT_PYPKG"])
    else:
      return 0
  #####################################################################
  @property 
  def stack_depth(self):
    if env_is_set("OBT_STACK"):
      return os.environ["OBT_STACK"].count("<")
    else:
      return 0
  #####################################################################

  def log(self,text):
    if self.quiet==False:
      print(text)

  #####################################################################

  def dump_env(self):
    for key in os.environ:
      if "OBT" in key:
        print(key,os.environ[key])

  def dump(self):

    print("##########################################################")
    print( "obtconfig.quiet: %s"%self.quiet )
    print( "obtconfig.inplace: %s"%self.inplace )
    print( "obtconfig.command: %s"%self._command )
    print( "obtconfig.numcores: %s"%self.num_cores )
    print( "obtconfig.stack_depth: %s"%self.stack_depth )
    print("##########################################################")
    print( "obtconfig.project_name: %s"%self.project_name )
    print( "obtconfig.project_dir: %s"%_ppath(self.project_dir ))
    print("##########################################################")
    print( "obtconfig.bin_priv_dir: %s"%_ppath(self.bin_priv_dir ))
    print( "obtconfig.bin_pub_dir: %s"%_ppath(self.bin_pub_dir ))
    print( "obtconfig.scripts_dir: %s"%_ppath(self.scripts_dir ))
    print( "obtconfig.build_dir: %s"%_ppath(self.build_dir ))
    print( "obtconfig.root_dir: %s"%_ppath(self.root_dir ))
    print( "obtconfig.stage_dir: %s"%_ppath(self.stage_dir ))
    print("##########################################################")
    print( "obtconfig.text_search_extensions: %s"%self.text_search_exts )
    print( "obtconfig.text_search_paths: %s"%_ppaths(self.text_search_path ))
    print("##########################################################")
    print( "obtconfig.modules_path: %s"%_ppaths(self.modules_path ))
    print( "obtconfig.dep_path: %s"%_ppaths(self.dep_path ))
    print("##########################################################")
    print( "obtconfig.original_ld_library_path: %s"%_ppaths(self.original_ld_library_path ))
    print( "obtconfig.original_python_paths: %s"%_ppaths(self.original_python_path ))
    print( "obtconfig.current_python_paths: %s"%_ppaths(self.python_path ))
    print( "obtconfig.python_home: %s"%_ppath(self.python_home ))
    print( "obtconfig.python_package_install_dir: %s"%_ppath(self.python_package_install_dir ))
    print("##########################################################")
    print( "obtconfig.subspace: %s"%self.subspace )
    print( "obtconfig.subspace_is_conda: %s"%self.subspace_is_conda )
    print( "obtconfig.subspace_dir: %s"%self.subspace_dir )
    print( "obtconfig.subspace_bin_dir: %s"%self.subspace_bin_dir )
    print( "obtconfig.subspace_lib_dir: %s"%self.subspace_lib_dir )
    print( "obtconfig.subspace_build_dir: %s"%_ppath(self.subspace_build_dir ))
    print("##########################################################")
    print( "obtconfig.VALID: %s"%self.valid )
    print("##########################################################")

  #####################################################################

  @property
  def valid(self):
    valid = (self.bin_priv_dir!=None)
    valid = valid and (self.bin_pub_dir!=None)
    valid = valid and (self.scripts_dir!=None)
    valid = valid and (self.root_dir!=None)
    valid = valid and (self.project_dir!=None)
    valid = valid and (self.stage_dir!=None)
    return valid


###############################################################################
#
###############################################################################

global _config
_config = ObtExecConfig() 

###########################################
# (EXPLICIT) initialize from command line arguments
###########################################

def configFromCommandLine(parser_args=None):

  def IS_ARG_SET(arg):
    if (parser_args!=None) and (arg in parser_args) and (parser_args[arg]!=None):
      return True
    else:
      return False

  ########################
  # independent items not attached to directories
  ########################

  if IS_ARG_SET("inplace") and parser_args["inplace"]:
    os.environ["OBT_INPLACE"] = "1"
    if "OBT_INPLACE" not in os.environ:
      di = _directoryOfInvokingModule()
      obt_folder = di/".."/"scripts/"/"obt"
      if(obt_folder.exists()):
        print("#######################################")
        print("YOU SHOULD USE --inplace if running OBT from a working copy!")
        print("#######################################")
        sys.exit(-1)

  if IS_ARG_SET("quiet") and parser_args["quiet"]:
    os.environ["OBT_QUIET"] = "1"

  if IS_ARG_SET("numcores"):
    numcores = int(parser_args["numcores"])
    os.environ["OBT_NUM_CORES"]=str(numcores)
  else:
    if "OBT_NUM_CORES" not in os.environ:
      numcores = multiprocessing.cpu_count()
      os.environ["OBT_NUM_CORES"]=str(numcores)

  if IS_ARG_SET("prompt"):
    os.environ["OBT_USE_PROMPT_PREFIX"] = parser_args["prompt"]

  os.environ["color_prompt"] = "yes"

  ########################
  # cache exterior env vars
  ########################
  def do_path(a,b):
    if env_is_set(a):
      os.environ[b] = os.environ[a] 
    else:
      os.environ[b] = ""

  if not env_is_set("OBT_ROOT"):
    os.environ["OBT_BIN_PUB_DIR"] = str(_directoryOfInvokingModule())
    os.environ["OBT_ROOT"] = str(_genpath(_config.bin_pub_dir/".."))

  if _config.inplace:
    scripts_dir = str(_genpath(_config.root_dir/"scripts")) 
    os.environ["OBT_BIN_PRIV_DIR"] = str(_genpath(_config.root_dir/"bin_priv"))
    os.environ["OBT_SCRIPTS_DIR"] = scripts_dir     
    sys.path = [scripts_dir]+sys.path
    orig_pyth_path = []
    if "PYTHONPATH" in os.environ:
      orig_pyth_path = os.environ["PYTHONPATH"].split(":")
    orig_pyth_paths = [scripts_dir]
    for x in orig_pyth_path:
      if x != "":
        orig_pyth_paths += [x]
    print(orig_pyth_paths)
    os.environ["PYTHONPATH"] = ":".join(orig_pyth_paths)
  else:
    for item in sys.path:
      if len(item):
        p = _genpath(item)
        try_scripts_dir = p/"obt"
        print(try_scripts_dir,try_scripts_dir.exists())
        if try_scripts_dir.exists():
          os.environ["OBT_SCRIPTS_DIR"] = str(_genpath(try_scripts_dir))
          #sys.path.append(str(_config.scripts_dir))

    do_path("PYTHONPATH","OBT_ORIGINAL_PYTHONPATH")

    os.environ["OBT_BIN_PRIV_DIR"] = str(_genpath(_config.root_dir/"obt"/"bin_priv"))

    do_path("PATH","OBT_ORIGINAL_PATH")
    do_path("LD_LIBRARY_PATH","OBT_ORIGINAL_LD_LIBRARY_PATH")
    do_path("PS1","OBT_ORIGINAL_PS1")
    
    #################################


    pypath = []

    if _config.inplace:
        ORIG_PYTHONPATHS = _config.original_python_path
        ORIG_PYTHONPATH0 = str(_config.original_python_path[0])
        if ORIG_PYTHONPATH0 in sys.path:
          sys.path.remove(ORIG_PYTHONPATH0)
    else:
      pass

    if env_is_set("OBT_ORIGINAL_PYTHONPATH"):
      pypath += os.environ["OBT_ORIGINAL_PYTHONPATH"].split(":")
    os.environ["PYTHONPATH"]=_pathlist_to_str(pypath)

    #################################

    if "PKG_CONFIG" in os.environ:
      os.environ["OBT_ORIGINAL_PKG_CONFIG"] = os.environ["PKG_CONFIG"]
    else :
      orig_pkg_config = findExecutable("pkg-config")
      if orig_pkg_config!=None:
        os.environ["OBT_ORIGINAL_PKG_CONFIG"] = str(orig_pkg_config)
      else:
        assert(False)

  if("PKG_CONFIG_PATH" not in os.environ):
    orig_pkg_config = findExecutable("pkg-config")
    if orig_pkg_config==None:
      print(deco.err("NO PKG-CONFIG FOUND, is your base shell setup correctly ?"))
      assert(False)
    pkg_config_result = subprocess.run(["pkg-config", "--variable=pc_path", "pkg-config"], capture_output=True, text=True)
    pkg_config_paths = []
    if pkg_config_result.returncode == 0:
      pkg_config_paths = pkg_config_result.stdout.strip().split(':')
      print(pkg_config_paths)
      os.environ["OBT_ORIGINAL_PKG_CONFIG_PATH"] = ":".join(pkg_config_paths)
      os.environ["PKG_CONFIG_PATH"] = ":".join(pkg_config_paths)
      print(os.environ)
  else:
    do_path("PKG_CONFIG_PATH","OBT_ORIGINAL_PKG_CONFIG_PATH")

  ########################
  # stage dir
  ########################

  if IS_ARG_SET("stagedir"):
    os.environ["OBT_STAGE"] = os.path.realpath(parser_args["stagedir"])

  assert(env_is_set("OBT_STAGE"))

  ########################
  # project dir
  ########################

  if not env_is_set("OBT_PROJECT_NAME"):
    os.environ["OBT_PROJECT_NAME"] = "OBT"

  if not env_is_set("OBT_PROJECT_DIR"):
    if IS_ARG_SET("project"):
      project_dir = parser_args["project"]
      project_dir = os.path.realpath(project_dir)
    else:
      project_dir = _config.root_dir
    os.environ["OBT_PROJECT_DIR"] = str(project_dir)

  assert(env_is_set("OBT_PROJECT_DIR"))

  ########################
  # subspace
  ########################

  if not env_is_set("OBT_SUBSPACE"):
    os.environ["OBT_SUBSPACE"] = "host"
    os.environ["OBT_SUBSPACE_PROMPT"] = "host"
  if IS_ARG_SET("subspace"):
    os.environ["OBT_SUBSPACE"] = parser_args["subspace"]
    os.environ["OBT_SUBSPACE_PROMPT"] = parser_args["subspace"]

  assert(env_is_set("OBT_SUBSPACE"))

  ########################

  if not env_is_set("OBT_MODULES_PATH"):
    if _config.inplace:
      os.environ["OBT_MODULES_PATH"] = str(_config.root_dir/"modules")
    else:
      os.environ["OBT_MODULES_PATH"] = str(_config.root_dir/"obt"/"modules")

  ########################

  if not env_is_set("OBT_PYTHONHOME"):
    os.environ["OBT_PYTHONHOME"] = str(_config.stage_dir/"pyvenv")

  ########################

  if IS_ARG_SET("sshkey"):
    GIT_SSH_COMMAND="ssh -i %s" % parser_args["sshkey"]
    _config._git_ssh_command = GIT_SSH_COMMAND

  ########################

  if IS_ARG_SET("command"):
    _config._command = parser_args["command"].split(" ")

  ########################
  # set up sys.path so we can import OBT modules
  ########################

  import obt.env
  import obt.path
  import obt.host
  import obt.dep
  import obt.subspace

  ########################

  obt.env.append("OBT_DEP_PATH",_config.modules_path[0]/"dep")

  ########################

  if IS_ARG_SET("stack"):
    stack_dir = Path(parser_args["stack"]).resolve()
    obt.env.append("OBT_STACK","<")
    assert(stack_dir.exists())
    assert( stack_dir == _config.stage_dir)

  #####################################################
  # setup os.environfrom config
  #####################################################

  obt.env.prepend("PATH",_config.bin_pub_dir )
  obt.env.prepend("PATH",_config.bin_priv_dir )

  if _config._git_ssh_command!=None:
    obt.env.set("GIT_SSH_COMMAND",_config._git_ssh_command)

  obt.env.set("PYTHONNOUSERSITE","TRUE")

  #####################################################

  if not env_is_set("OBT_SEARCH_EXTLIST"):
    os.environ["OBT_SEARCH_EXTLIST"] = ".cpp:.c:.cc:.h:.hpp:.inl:.qml:.m:.mm:.py:.txt:.glfx"
  if not env_is_set("OBT_SEARCH_PATH"):
    os.environ["OBT_SEARCH_PATH"] = ""

  #####################################################
  # items only valid if there is a staging folder
  #####################################################
  
  if _config.valid: # Valid StageDir ?
    obt.env.prepend("PATH",_config.stage_dir/"bin")
    obt.env.prepend("LD_LIBRARY_PATH",_config.stage_dir/"lib")
    obt.env.prepend("LD_LIBRARY_PATH",_config.stage_dir/"lib64")
    obt.env.prepend("PKG_CONFIG",_config.stage_dir/"bin"/"pkg-config")
    obt.env.prepend("PKG_CONFIG_PATH",_config.stage_dir/"lib"/"pkgconfig")
    obt.env.prepend("PKG_CONFIG_PATH",_config.stage_dir/"lib64"/"pkgconfig")
    #obt.env.prepend("PYTHONPATH",_config.stage_dir/"lib"/"python")
    print(os.environ)
    ########################

    # subspace paths
    subspace_dir = _config.stage_dir
    if _config.subspace!="host":
      subspace_dir = obt.subspace.descriptor(_config.subspace)._prefix
    os.environ["OBT_SUBSPACE_DIR"] = str(subspace_dir)
    os.environ["OBT_SUBSPACE_LIB_DIR"] = str(_config.subspace_lib_dir)
    os.environ["OBT_SUBSPACE_BIN_DIR"] = str(_config.subspace_bin_dir)
    os.environ["OBT_BUILDS"] = str(_config.build_dir)
    os.environ["OBT_SUBSPACE_BUILD_DIR"] = str(_config.subspace_build_dir)

    if _config.project_dir!=_config.root_dir:
      _config.dump_env()
      importProject(_config)

  #####################################################
  return _config

###########################################
# (IMPLICIT) default config (from environment)
###########################################

def configFromEnvironment():
  return _config

###########################################
# per dep dynamic env init
###########################################

def initializeDependencyEnvironments(envsetup):

  import obt.host
  import obt.dep
  import obt.sdk
  import obt.subspace

  ####################################
  hostinfo = obt.host.description()
  if hasattr(hostinfo,"env_init"):
    hostinfo.env_init()
  ####################################
  sdkitems = obt.sdk.enumerate()
  for sdk_module_key in sdkitems.keys():
    sdk_module_item = sdkitems[sdk_module_key]
    sdk_module = sdk_module_item._module
    sdkinfo = sdk_module.sdkinfo()
    if hasattr(sdkinfo,"env_init"):
      sdkinfo.env_init()
  ####################################
  depitems = obt.dep.DepNode.FindWithMethod("env_init")
  for depitemk in depitems:
    depitem = depitems[depitemk]
    if depitem.supports_host:
      depitem.env_init()
  ####################################
  subspaceitems = obt.subspace.findWithMethod("env_init")
  for subitemk in subspaceitems:
    subitem = subspaceitems[subitemk]
    subitem._module.env_init(envsetup)
  ####################################
