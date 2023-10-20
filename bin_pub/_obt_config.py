#!/usr/bin/env python3
###############################################################################
# Orkid Build System
# Copyright 2010-2023, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, sys, argparse, inspect, pathlib, multiprocessing, json, importlib
Path = pathlib.Path

###########################################
# need private copy of InvokingModule fns
###########################################

def _genpath(inp):
  return pathlib.Path(os.path.realpath(str(inp)))

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

  try_project_manifest = config._project_dir/"obt.project"/"obt.manifest"

  if try_project_manifest.exists():
    manifest_json = json.load(open(try_project_manifest,"r"))
    #print(manifest_json)
    config._project_name = manifest_json["name"]
    autoexec = manifest_json["autoexec"]
    autoexec = config._project_dir/"obt.project"/autoexec
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
#
###########################################

###########################################
# The location of this config module is in bin_pub because it needs to be available:
#   1. from outside of an OBT environment 
#   2. AND early in script startup (before sys.paths are setup)
# This also implies this config object cannot import OBT modules itself (self contained)
###########################################

class ObtExecConfig(object):

  #####################################################################

  def __init__(self): # default initialization from env vars
    self._bin_priv_dir = None 
    self._bin_pub_dir = None
    self._scripts_dir = None
    self._root_dir = None
    self._project_dir = None
    self._project_bin_dir = None
    self._project_name = "obt"
    self._stage_dir = None
    self._build_dir = None
    self._inplace = False
    self._stack_depth = 0
    self._quiet = False
    self._command = None
    self._subspace = None
    self._subspace_dir = None
    self._subspace_bin_dir = None
    self._subspace_lib_dir = None
    self._subspace_is_conda = False
    self._did_override_pythonpath = False
    self._text_search_paths = []
    self._text_search_exts = ".cpp:.c:.cc:.h:.hpp:.inl:.qml:.m:.mm:.py:.txt:.glfx".split(" ")
    self._dep_paths = []
    self._module_paths = []
    self._numcores = 1
    self._prompt_prefix = None
    self._disable_syspypath = True
    self._git_ssh_command = None

    self._original_ld_library_paths = []
    self._original_python_paths = []
    self._original_paths = []
    self._original_prompt = []

    if "OBT_ROOT" in os.environ:
      self._root_dir = _genpath(os.environ["OBT_ROOT"])

    if (self._root_dir!=None):
      if "OBT_INPLACE" in os.environ:
        self._inplace = True
        self._bin_priv_dir = self._root_dir/"obt"/"bin_priv"
        self._bin_pub_dir = self._root_dir/"bin_pub"
      else:
        self._bin_priv_dir = self._root_dir/"obt"/"bin_priv"
        self._bin_pub_dir = self._root_dir/"bin_pub"

    self.setupOriginalPaths()

    ##########################################

    if "OBT_SEARCH_PATH" in os.environ:
      self._text_search_paths = os.environ["OBT_SEARCH_PATH"].split(":")
      self._text_search_paths = [_genpath(s) for s in self._text_search_paths if s]
    if "OBT_SEARCH_EXTLIST" in os.environ:
      self._text_search_exts = os.environ["OBT_SEARCH_EXTLIST"].split(":")
      self._text_search_exts = [s for s in self._text_search_exts if s]
    if "OBT_DEP_PATH" in os.environ:
      self._dep_paths = os.environ["OBT_DEP_PATH"].split(":")
      self._dep_paths = [_genpath(s) for s in self._dep_paths if s]
    if "OBT_MODULES_PATH" in os.environ:
      self._module_paths = os.environ["OBT_MODULES_PATH"].split(":")
      self._module_paths = [_genpath(s) for s in self._module_paths if s]

    if "OBT_STAGE" in os.environ:
      self._stage_dir = _genpath(os.environ["OBT_STAGE"])
    if "OBT_BUILDS" in os.environ:
      self._build_dir = _genpath(os.environ["OBT_BUILDS"])

    if "OBT_SCRIPTS_DIR" in os.environ:
      self._scripts_dir = _genpath(os.environ["OBT_SCRIPTS_DIR"])
      sys.path.append(str(self._scripts_dir))

    if "OBT_PROJECT_DIR" in os.environ:
      self._project_dir = _genpath(os.environ["OBT_PROJECT_DIR"])
    if "OBT_PROJECT_NAME" in os.environ:
      self._project_name = os.environ["OBT_PROJECT_NAME"]
    if "OBT_NUM_CORES" in os.environ:
      self._numcores = int(os.environ["OBT_NUM_CORES"])
    if "OBT_SUBSPACE" in os.environ:
      self._subspace = os.environ["OBT_SUBSPACE"]
    if "OBT_SUBSPACE_DIR" in os.environ:
      self._subspace_dir = _genpath(os.environ["OBT_SUBSPACE_DIR"])
      self._subspace_is_conda = "conda" in os.environ["OBT_SUBSPACE_DIR"]
    if "OBT_SUBSPACE_BIN_DIR" in os.environ:
      self._subspace_bin_dir = _genpath(os.environ["OBT_SUBSPACE_BIN_DIR"])
    if "OBT_SUBSPACE_LIB_DIR" in os.environ:
      self._subspace_lib_dir = _genpath(os.environ["OBT_SUBSPACE_LIB_DIR"])

  #####################################################################

  def setupOriginalPaths(self):

    ########################
    # binary search paths
    ########################

    if "PATH" in os.environ:
      self._original_paths = os.environ["PATH"].split(":")
      self._original_paths = [_genpath(s) for s in self._original_paths if s]
    # override with OBT_ORIGINAL_PATH if present
    if "OBT_ORIGINAL_PATH" in os.environ:
      self._original_paths = os.environ["OBT_ORIGINAL_PATH"].split(":")
      self._original_paths = [_genpath(s) for s in self._original_paths if s]

    if "LD_LIBRARY_PATH" in os.environ:
      self._original_ld_library_paths = os.environ["LD_LIBRARY_PATH"].split(":")
      self._original_ld_library_paths = [_genpath(s) for s in self._original_ld_library_paths if s]
    # override with OBT_ORIGINAL_LD_LIBRARY_PATH if present
    if "OBT_ORIGINAL_LD_LIBRARY_PATH" in os.environ:
      self._original_ld_library_paths = os.environ["OBT_ORIGINAL_LD_LIBRARY_PATH"].split(":")
      self._original_ld_library_paths = [_genpath(s) for s in self._original_ld_library_paths if s]

    ########################
    # pkgconfig
    ########################

    orig_pkg_config_path = None
    #orig_pkg_config_path = obt.command.capture(["pkg-config","--variable","pc_path","pkg-config"])
    #orig_pkg_config_path = orig_pkg_config_path.replace("\n","")
    #print("orig_pkg_config_path<%s>"%orig_pkg_config_path)

    if "OBT_ORIGINAL_PKG_CONFIG" in os.environ:
      orig_pkg_config = os.environ["OBT_ORIGINAL_PKG_CONFIG"]
    else:
      if "PKG_CONFIG" in os.environ:
        orig_pkg_config = os.environ["PKG_CONFIG"]
        os.environ["OBT_ORIGINAL_PKG_CONFIG"] = orig_pkg_config
      else :
        orig_pkg_config = findExecutable("pkg-config")
        if orig_pkg_config!=None:
          os.environ["OBT_ORIGINAL_PKG_CONFIG"] = str(orig_pkg_config)
        else:
          assert(False)

    if "OBT_ORIGINAL_PKG_CONFIG_PATH" in os.environ:
      orig_pkg_config_path = os.environ["OBT_ORIGINAL_PKG_CONFIG_PATH"]
    else:
      if "PKG_CONFIG_PATH" in os.environ:
        orig_pkg_config_path = os.environ["PKG_CONFIG_PATH"].split(":")
    
    if orig_pkg_config_path!=None:
      orig_pkg_config_path = [_genpath(s) for s in orig_pkg_config_path if s]

    ########################
    # python
    ########################

    if "PYTHONPATH" in os.environ:
      ORIG_PYTHONPATHS = os.environ["PYTHONPATH"].split(":")
      ORIG_PYTHONPATHS = [_genpath(s) for s in ORIG_PYTHONPATHS if s]
      self._original_python_paths = ORIG_PYTHONPATHS

  #####################################################################

  def log(self,text):
    if self._quiet==False:
      print(text)

  #####################################################################

  def dump(self):

    for key in os.environ:
      if "OBT" in key:
        print(key,os.environ[key])
    print("##########################################################")
    print( "obtconfig.quiet: %s"%self._quiet )
    print( "obtconfig.inplace: %s"%self._inplace )
    print( "obtconfig.command: %s"%self._command )
    print( "obtconfig.numcores: %s"%self._numcores )
    print( "obtconfig.did_override_pythonpath: %s"%self._did_override_pythonpath )
    print("##########################################################")
    print( "obtconfig.project_name: %s"%self._project_name )
    print( "obtconfig.project_dir: %s"%_ppath(self._project_dir ))
    print("##########################################################")
    print( "obtconfig.bin_priv_dir: %s"%_ppath(self._bin_priv_dir ))
    print( "obtconfig.bin_pub_dir: %s"%_ppath(self._bin_pub_dir ))
    print( "obtconfig.scripts_dir: %s"%_ppath(self._scripts_dir ))
    print( "obtconfig.build_dir: %s"%_ppath(self._build_dir ))
    print( "obtconfig.root_dir: %s"%_ppath(self._root_dir ))
    print( "obtconfig.stage_dir: %s"%_ppath(self._stage_dir ))
    print("##########################################################")
    print( "obtconfig.text_search_extensions: %s"%self._text_search_exts )
    print( "obtconfig.text_search_paths: %s"%_ppaths(self._text_search_paths ))
    print("##########################################################")
    print( "obtconfig.module_paths: %s"%_ppaths(self._module_paths ))
    print( "obtconfig.dep_paths: %s"%_ppaths(self._dep_paths ))
    print("##########################################################")
    print( "obtconfig.original_ld_library_paths: %s"%_ppaths(self._original_ld_library_paths ))
    print( "obtconfig.original_python_paths: %s"%_ppaths(self._original_python_paths ))
    print("##########################################################")
    print( "obtconfig.subspace: %s"%self._subspace )
    print( "obtconfig.subspace_is_conda: %s"%self._subspace_is_conda )
    print( "obtconfig.subspace_dir: %s"%self._subspace_dir )
    print( "obtconfig.subspace_bin_dir: %s"%self._subspace_bin_dir )
    print( "obtconfig.subspace_lib_dir: %s"%self._subspace_lib_dir )
    print("##########################################################")
    print( "obtconfig.VALID: %s"%self.valid )
    print("##########################################################")

  #####################################################################

  @property
  def valid(self):
    valid = (self._bin_priv_dir!=None)
    valid = valid and (self._bin_pub_dir!=None)
    valid = valid and (self._bin_pub_dir!=None)
    valid = valid and (self._scripts_dir!=None)
    valid = valid and (self._root_dir!=None)
    valid = valid and (self._project_dir!=None)
    valid = valid and (self._stage_dir!=None)
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

  ########################

  def IS_ARG_SET(arg):
    if parser_args==None:
      return False
    return arg in parser_args and parser_args[arg]!=None

  ########################

  if IS_ARG_SET("inplace"):
    _config._inplace = parser_args["inplace"]

  ########################

  if IS_ARG_SET("sshkey"):
    GIT_SSH_COMMAND="ssh -i %s" % parser_args["sshkey"]
    _config._git_ssh_command = GIT_SSH_COMMAND

  ########################

  if IS_ARG_SET("command"):
    _config._command = parser_args["command"].split(" ")

  ########################

  if IS_ARG_SET("quiet"):
    _config._quiet = parser_args["quiet"]

  ########################

  _config.setupOriginalPaths()

  ########################

  _config._bin_pub_dir = _directoryOfInvokingModule()
  _config._root_dir = _genpath(_config._bin_pub_dir/"..")

  if _config._inplace:
    _config._bin_priv_dir = _genpath(_config._root_dir/"bin_priv")
    _config._scripts_dir = _genpath(_config._root_dir/"scripts")
  else:
    _config._bin_priv_dir = _genpath(_config._root_dir/"obt"/"bin_priv")
    _config._scripts_dir = _genpath(_config._root_dir/"obt"/"scripts")

  ########################
  # set up sys.path so we can import OBT modules
  ########################

  sys.path = [str(_config._scripts_dir)]+sys.path

  import obt.env
  import obt.path
  import obt.host
  import obt.dep

  ########################

  if IS_ARG_SET("stack"):
    try_staging = Path(parser_args["stack"]).resolve()
    obt.env.append("OBT_STACK","<")
    _config._stack_depth = os.environ["OBT_STACK"].count("<")
    assert(try_staging.exists())
    _config._stage_dir = try_staging
  
  if IS_ARG_SET("stagedir"):
    _config._stage_dir = pathlib.Path(os.path.realpath(parser_args["stagedir"]))

  if _config._stage_dir!=None:
    _config._build_dir = _config._stage_dir/"builds"

  ########################

  if IS_ARG_SET("numcores"):
    _config._numcores = int(parser_args["numcores"])
    os.environ["OBT_NUM_CORES"]=str(_config._numcores)
  else:
    if "OBT_NUM_CORES" not in os.environ:
      NumCores = multiprocessing.cpu_count()
      _config._numcores = NumCores

  ########################

  if IS_ARG_SET("prompt"):
    _config._prompt_prefix = parser_args["prompt"]

  ########################

  if IS_ARG_SET("project"):
    project_dir = parser_args["project"]
    project_dir = os.path.realpath(project_dir)
    _config._project_dir = pathlib.Path(project_dir)
  else:
    _config._project_dir = _config._root_dir

  ########################

  if _config._inplace:
    if "PYTHONPATH" in os.environ:
      ORIG_PYTHONPATHS = os.environ["PYTHONPATH"].split(":")
      ORIG_PYTHONPATHS = [_genpath(s) for s in ORIG_PYTHONPATHS if s]
      #print(ORIG_PYTHONPATHS)
      #print(sys.path)
      _config._original_python_paths = ORIG_PYTHONPATHS
      ORIG_PYTHONPATH = str(_config._original_python_paths[0])
      if ORIG_PYTHONPATH in sys.path:
        sys.path.remove(ORIG_PYTHONPATH)
    
    _config._did_override_pythonpath = True
    os.environ["PYTHONPATH"]=str(_config._scripts_dir)
    #os.environ["PATH"]=str(root_dir/"bin_priv")+":"+os.environ["PATH"]
    sys.path = [str(_config._scripts_dir)]+sys.path

  ########################

  if _config._project_dir==None:
    _config._project_dir = _config._root_dir
  
  ########################

  assert(str(_config._project_dir)!="/nvme4/aphidsystems/ork.build")

  if _config._inplace:
    _config._module_paths = [_config._root_dir/"modules"]
  else:
    _config._module_paths = [_config._root_dir/"obt"/"modules"]

  #####################################################
  # setup os.environfrom config
  #####################################################

  if _config._quiet:
    os.environ["OBT_QUIET"]="1"
  if _config._inplace:
    os.environ["OBT_INPLACE"]="1"
  
  #assert(_config.valid)

  os.environ["OBT_ROOT"]=str(_config._root_dir)
  os.environ["OBT_PROJECT_DIR"]=str(_config._project_dir)
  os.environ["OBT_ORIGINAL_PYTHONPATH"]=str(_config._project_dir)
  os.environ["OBT_NUM_CORES"]=str(_config._numcores)
  os.environ["OBT_SCRIPTS_DIR"] = str(_config._scripts_dir) 
  os.environ["OBT_SUBSPACE"] = "host"
  os.environ["OBT_SUBSPACE_PROMPT"] = "host"
  os.environ["OBT_PROJECT_NAME"] = str(_config._project_name)
  os.environ["OBT_MODULES_PATH"] = ":".join(_listToStrList(_config._module_paths))
  os.environ["color_prompt"] = "yes"
  os.environ["OBT_SEARCH_EXTLIST"] = ":".join(_config._text_search_exts)
  os.environ["OBT_SEARCH_PATH"] = ":".join(_listToStrList(_config._text_search_paths))

  os.environ["OBT_BIN_PUB"] = str(_config._bin_pub_dir)
  os.environ["OBT_BIN_PRIVATE"] = str(_config._bin_priv_dir)

  obt.env.prepend("PATH",_config._bin_pub_dir )
  obt.env.prepend("PATH",_config._bin_priv_dir )

  #obt.env.append("OBT_MODULES_PATH",obt.path.modules())
  obt.env.append("OBT_DEP_PATH",obt.path.modules()/"dep")
  #os.environ["OBT_ORIGINAL_PATH"] = orig_path 
  #os.environ["OBT_ORIGINAL_LD_LIBRARY_PATH"] = orig_ld_library_path
  #os.environ["OBT_ORIGINAL_PS1"] = orig_ps1

  if _config._prompt_prefix != None:
    os.environ["OBT_USE_PROMPT_PREFIX"] = _config._prompt_prefix

  if _config._git_ssh_command!=None:
    obt.env.set("GIT_SSH_COMMAND",_config._git_ssh_command)

  obt.env.set("PYTHONNOUSERSITE","TRUE")
  obt.env.append("PYTHONPATH",_config._scripts_dir)

  #####################################################
  # items only valid if there is a staging folder
  #####################################################

  if _config.valid: # Valid StageDir ?
    os.environ["OBT_STAGE"]=str(_config._stage_dir)
    os.environ["OBT_BUILDS"]=str(_config._build_dir)
    os.environ["OBT_PYTHONHOME"] = str(_config._stage_dir/"pyvenv")
    os.environ["OBT_SUBSPACE_LIB_DIR"] = str(_config._stage_dir/"lib")
    os.environ["OBT_SUBSPACE_BIN_DIR"] = str(_config._stage_dir/"bin")
    os.environ["OBT_SUBSPACE_DIR"] = str(_config._stage_dir)
    obt.env.prepend("PATH",_config._stage_dir/"bin")
    obt.env.prepend("LD_LIBRARY_PATH",_config._stage_dir/"lib")
    obt.env.prepend("LD_LIBRARY_PATH",_config._stage_dir/"lib64")
    obt.env.prepend("PKG_CONFIG",_config._stage_dir/"bin"/"pkg-config")
    #obt.env.prepend("PKG_CONFIG_PREFIX",_config._stage_dir)
    obt.env.prepend("PKG_CONFIG_PATH",_config._stage_dir/"lib"/"pkgconfig")
    obt.env.prepend("PKG_CONFIG_PATH",_config._stage_dir/"lib64"/"pkgconfig")
    obt.env.prepend("PYTHONPATH",_config._stage_dir/"lib"/"python")
    obt.env.append("LD_LIBRARY_PATH",_config._stage_dir/"python-3.9.13"/"lib")

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
