#!/usr/bin/env python3
###############################################################################
# Orkid Build System
# Copyright 2010-2023, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, sys, argparse, inspect, pathlib, subprocess, multiprocessing, json, importlib, site
import importlib.resources
from functools import lru_cache

Path = pathlib.Path

from obt.deco import Deco 

deco = Deco()

###########################################

def __get_obt_root():
 return importlib.resources.files('obt')

def is_inplace():
  git_folder = __get_obt_root()/".."/".."/".git"
  return os.path.exists(git_folder)

##########################################

@lru_cache(maxsize=None)
def obt_data_base():
  if is_inplace():
    dbase = __get_obt_root()/".."/".."
    return Path(os.path.normpath(dbase))
  else:
    assert("VIRTUAL_ENV" in os.environ)
    p = Path(os.environ["VIRTUAL_ENV"])/"obt"
    assert(p.exists())
    return p
 
##########################################

def __get_modules():
  return obt_data_base()/"modules"

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

def importProject(item):

  project_dirs = []
  
  try_project_manifest = item/"obt.project"/"obt.manifest"

  if try_project_manifest.exists():
    manifest_json = json.load(open(try_project_manifest,"r"))
    project_name = manifest_json["name"]
    #print(manifest_json)
    #config._project_name = manifest_json["name"]
    autoexec = manifest_json["autoexec"]
    autoexec = item/"obt.project"/autoexec
    #print(autoexec)
    assert(autoexec.exists())

    modules = item/"obt.project"/"modules"
    if modules.exists():
      os.environ["OBT_MODULES_PATH"] = os.environ["OBT_MODULES_PATH"] + ":" + str(modules)
    dep = item/"obt.project"/"modules"/"dep"
    if dep.exists():
      os.environ["OBT_DEP_PATH"] = os.environ["OBT_DEP_PATH"] + ":" + str(dep)

    # import autoexec as python module
    spec = importlib.util.spec_from_file_location("autoexec", str(autoexec))
    init_env = importlib.util.module_from_spec(spec) 
    spec.loader.exec_module(init_env)
    print(deco.orange("############################################################################################"))    
    print(deco.orange("Initializing Project: %s"%project_name))
    print(deco.orange("############################################################################################"))    
    init_env.setup()
    print(deco.orange("############################################################################################"))    
    print(deco.orange("Initialized Project: %s"%project_name))
    print(deco.orange("############################################################################################"))    
    if "extend_bashrc" in dir(init_env):
      BASHEXT = init_env.extend_bashrc()
      _config.addBashRcLines(BASHEXT)

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
    self._project_dirs = []
    self._bashrc_lines = []
  #####################################################################
  def addBashRcLines(self,lines):
    self._bashrc_lines += lines
  #####################################################################
  @property 
  def num_cores(self):
    return os.environ["OBT_NUM_CORES"]
  #####################################################################
  @property 
  def inplace(self):
    return is_inplace()
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
  def obt_scripts_base():
    if "OBT_SCRIPTS_DIR" in os.environ:
      return Path(os.environ["OBT_SCRIPTS_DIR"])
    else:
      # search sys.path for "obt"
      for item in sys.path:
        obt_subfolder_exists = (_genpath(item)/"obt").exists()
        if obt_subfolder_exists:
          return Path(item)
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
    valid = valid and (self.stage_dir!=None)
    return valid


###############################################################################
#
###############################################################################

global _config
_config = ObtExecConfig() 

def obt_scripts_base():
  if "OBT_SCRIPTS_DIR" in os.environ:
    return Path(os.environ["OBT_SCRIPTS_DIR"])
  else:
    import importlib.util
    obt_spec = importlib.util.find_spec("obt")
    obt_base = Path(obt_spec.submodule_search_locations[0])
    #print(obt_base)
    return obt_base

###########################################
# (EXPLICIT) initialize (bootstrap) from command line arguments
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

  if is_inplace():
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

  ########################
  norm_venvpackages = os.path.normpath(str(site.getsitepackages()[0]))
  norm_pypath = os.path.normpath(str(obt_scripts_base()/".."))
  os.environ["PYTHONPATH"] = norm_venvpackages + ":" + norm_pypath
  os.environ["OBT_VENV_DIR"] = os.environ["VIRTUAL_ENV"]
  os.environ["OBT_VENV_DATA"] = str(obt_data_base())
  ########################

  if not env_is_set("OBT_ORIGINAL_PYTHONPATH"):
    os.environ["OBT_ORIGINAL_PYTHONPATH"] = norm_venvpackages
  
  if not env_is_set("OBT_ROOT"):
    os.environ["OBT_BIN_PUB_DIR"] = str(_directoryOfInvokingModule())
    os.environ["OBT_ROOT"] = str(obt_data_base())

  # find obt.scripts dir using python module search
  if not env_is_set("OBT_SCRIPTS_DIR"):
    os.environ["OBT_SCRIPTS_DIR"] = str(obt_scripts_base())
    os.environ["OBT_BIN_PRIV_DIR"] = str(obt_data_base()/"bin_priv")
   
    #do_path("PYTHONPATH","OBT_ORIGINAL_PYTHONPATH")
    do_path("PATH","OBT_ORIGINAL_PATH")
    do_path("LD_LIBRARY_PATH","OBT_ORIGINAL_LD_LIBRARY_PATH")
    do_path("PS1","OBT_ORIGINAL_PS1")
          
    #################################

    if "PKG_CONFIG" in os.environ:
      os.environ["OBT_ORIGINAL_PKG_CONFIG"] = os.environ["PKG_CONFIG"]
    else :
      orig_pkg_config = findExecutable("pkg-config")
      if orig_pkg_config!=None:
        os.environ["OBT_ORIGINAL_PKG_CONFIG"] = str(orig_pkg_config)
      else:
        print(deco.err("NO PKG-CONFIG FOUND, is your base shell setup correctly ?"))      
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
      #print(pkg_config_paths)
      os.environ["OBT_ORIGINAL_PKG_CONFIG_PATH"] = ":".join(pkg_config_paths)
      os.environ["PKG_CONFIG_PATH"] = ":".join(pkg_config_paths)
      #print(os.environ)
  else:
    do_path("PKG_CONFIG_PATH","OBT_ORIGINAL_PKG_CONFIG_PATH")

  ########################
  # stage dir
  ########################

  if IS_ARG_SET("stagedir"):
    os.environ["OBT_STAGE"] = os.path.realpath(parser_args["stagedir"])

  assert(env_is_set("OBT_STAGE"))

  ########################
  # project dir(s)
  ########################

  if not env_is_set("OBT_PROJECT_NAME"):
    os.environ["OBT_PROJECT_NAME"] = "OBT"

  if IS_ARG_SET("project"):
    project_dirs = parser_args["project"]
    print(project_dirs)
    _config._project_dirs = _genpaths(":".join(project_dirs))
    os.environ["OBT_PROJECT_DIRS"] = ":".join(project_dirs)

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
    os.environ["OBT_MODULES_PATH"] = str(obt_data_base()/"modules")

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
  print(deco.orange("############################################################################################"))    
  print(deco.orange("Initializing OBT Base"))
  print(deco.orange("############################################################################################"))    
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
    obt.env.set("OBT_SEARCH_EXTLIST",".cpp:.c:.cc:.h:.hpp:.inl:.qml:.m:.mm:.py:.txt:.glfx")
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
    #print(os.environ)
    ########################

    print(deco.orange("############################################################################################"))    
    print(deco.orange("Initialized OBT Base"))
    print(deco.orange("############################################################################################"))    

    for item in _config._project_dirs:
      if item!=_config.root_dir:
        importProject(item)
        #_config.dump_env()

    subspace_dir = _config.stage_dir

    # subspace paths
    if _config.subspace!="host":
      subspace_dir = obt.subspace.descriptor(_config.subspace)._prefix

    def updateSUBS():
      obt.env.set("OBT_SUBSPACE_DIR",str(subspace_dir))
      obt.env.set("OBT_SUBSPACE_LIB_DIR",str(_config.subspace_lib_dir))
      obt.env.set("OBT_SUBSPACE_BIN_DIR",str(_config.subspace_bin_dir))
      obt.env.set("OBT_BUILDS",str(_config.build_dir))
      obt.env.set("OBT_SUBSPACE_BUILD_DIR",str(_config.subspace_build_dir))

    updateSUBS()


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
  print(deco.orange("############################################################################################"))    
  print(deco.orange("Initializing Dependencies"))
  print(deco.orange("############################################################################################"))    
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
  print(deco.orange("############################################################################################"))    
  print(deco.orange("Initialized Dependencies"))
  print(deco.orange("############################################################################################"))    
