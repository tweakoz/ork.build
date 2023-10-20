import os, atexit, json, sys
import socket

global log_node_stack  
global jsonroot

hostname = socket.gethostname()
jsonroot = list()
curwd = os.getcwd()
curpid = os.getpid()

topenv = dict(os.environ)


log_node_stack = list()
log_node_stack.append(jsonroot)

def stage_dir():
  if "OBT_STAGE" in os.environ.keys():
	  return os.environ["OBT_STAGE"]
  else:
    return None


FORBIDDEN_KEYS = ["SESSION_MANAGER","SSH_AUTH_SOCK","DESKTOP_SESSION","SSH_AGENT_PID","XDG_SESSION_DESKTOP"]
FORBIDDEN_KEYS += ["XDG_SESSION_TYPE","GPG_AGENT_INFO","VTE_VERSION","GNOME_TERMINAL_SCREEN"]
FORBIDDEN_KEYS += ["INVOCATION_ID","MANAGERPID","GNOME_TERMINAL_SERVICE","JOURNAL_STREAM"]
FORBIDDEN_KEYS += ["SDKMAN_VERSION","XDG_MENU_PREFIX","SBT_HOME","JAVA_HOME","XDG_CURRENT_DESKTOP"]
FORBIDDEN_KEYS += ["SDKMAN_CANDIDATES_API","SDKMAN_CANDIDATES_DIR","GDMSESSION"]
FORBIDDEN_KEYS += ["SDKMAN_PLATFORM","DBUS_SESSION_BUS_ADDRESS","XDG_RUNTIME_DIR","XDG_DATA_DIRS"]
FORBIDDEN_KEYS += ["XDG_CONFIG_DIRS","XDG_MENU_PREFIX","GNOME_DESKTOP_SESSION_ID","MANDATORY_PATH","GTK_MODULES"]
FORBIDDEN_KEYS += ["XDG_SESSION_CLASS","DEFAULTS_PATH","LESSOPEN","LESSCLOSE","TERM","DISPLAY","XMODIFIERS","XAUTHORITY"]
FORBIDDEN_KEYS += ["USER","HOME", "SDKMAN_DIR","SHELL","COLORTERM","EDITOR","GJS_DEBUG_TOPICS","GJS_DEBUG_OUTPUT","WINDOWPATH"]

################################################
# attempt to cleanse private info out of strings
################################################

def cleanseString(the_string):
  stage_as_str = stage_dir()
  home_as_str = str(os.environ["HOME"])
  user_as_str = str(os.environ["USER"])
  uid = os.getuid()
  usrrundir_as_str = "/run/user/%d"%uid
  ########################
  found = the_string.find(stage_as_str)
  if found >= 0:
    the_string = the_string.replace(stage_as_str,"${OBT_STAGE}")
  ########################
  found = the_string.find(home_as_str)
  if found >= 0:
    the_string = the_string.replace(home_as_str,"${HOME}")
  ########################
  if( "ORKID_WORKSPACE_DIR" in os.environ.keys() ):
    owsr_as_str = str(os.environ["ORKID_WORKSPACE_DIR"])
    found = the_string.find(owsr_as_str)
    if found >= 0:
      the_string = the_string.replace(owsr_as_str,"${OWSDIR}")
  ########################
  found = the_string.find(usrrundir_as_str)
  if found >= 0:
    the_string = the_string.replace(usrrundir_as_str,"${USERRUNDIR}")
  ########################
  found = the_string.find(user_as_str)
  if found >= 0:
    the_string = the_string.replace(user_as_str,"${USER}")
  ########################
  found = the_string.find(curwd)
  if found >= 0:
    the_string = the_string.replace(curwd,"${TOPEXECDIR}")
  ########################
  found = the_string.find(hostname)
  if found >= 0:
    the_string = the_string.replace(hostname,"${HOSTNAME}")
  return the_string

################################################

def iterlist(the_list):
  newl = list()
  for v in the_list:
    if isinstance(v,str):
      v = cleanseString(v)
    else:
      v = str(v)
      v = cleanseString(v)
    newl.append(v)
  return newl

################################################

def iterdict(the_dict,pard=None,park=None):
 ####################################
 def _iterlist(the_list):
  newl = list()
  for v in the_list:
   if isinstance(v, dict):
    v = iterdict(v,pard,park)
   elif isinstance(v, list):
    v = _iterlist(v)
   elif isinstance(v,str):
     v = cleanseString(v)
   else:
     v = str(v)
     v = cleanseString(v)
   newl.append(v)
  return newl
 ####################################
 newd = dict()
 ####################################
 for k, v in the_dict.items():
  add = True
  if isinstance(v, dict):
    v = iterdict(v,the_dict,k)
  elif isinstance(v, list):
    v = _iterlist(v)
  else:
    if type(v) != str:
      v = str(v)
    v = cleanseString(v)
    if pard!=None and park!=None:
      if park=="os_env":
        if k in topenv:
          add = (v != cleanseString(str(topenv[k])))
          #print("match<k:%s> <v:%s> <te:%s> : %d"%(k,v,topenv[k], int(add)))
  if k in FORBIDDEN_KEYS:
  	add = False
  if add:
    newd[k] = v
 return newd  

################################################

def buildTrace(item):
  index = len(log_node_stack)-1
  top = log_node_stack[index]
  top.append(item)

################################################

class NestedBuildTrace(object):
  def __init__(self, item):
    self._item = item

  def __enter__(self):
    index = len(log_node_stack)-1
    top = log_node_stack[index]
    top.append(self._item)
    subops = list()
    self._item["subops"] = subops
    log_node_stack.append(subops)
    return self

  def __exit__(self, etype, value, traceback):
    log_node_stack.pop()


################################################

def proc_list(the_list):
  newlist = list()
  for item in the_list:
   newlist.append(iterdict(item))
  return newlist 

################################################

def savelog():
  import obt._globals as _glob
  if _glob.isBuildTraceEnabled():
    steplogfile = "%s/buildlogs/obtdump-%d.json"%(stage_dir(),curpid)
    copy = list(jsonroot)
    processed = list()
    ##############################
    # write top level environment to log file
    ##############################
    processed += [{ "topenv": iterdict(topenv) }]
    processed += [{ "sysargv": iterlist(sys.argv) }]
    ##############################
    # process dictionary before logging
    ##############################
    processed += proc_list(copy)
    ##############################
    # write it out
    ##############################
    with open(str(steplogfile),"w") as f:
      as_str = json.dumps(processed, indent=2)
      f.write(as_str)

atexit.register(savelog)
