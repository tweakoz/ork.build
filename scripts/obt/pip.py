import os, shutil
import obt.deco
from obt import path, dep
from obt.command import Command

def _clean_build_dir(name_or_list):
  """Remove build/ directory for local path installs to avoid stale artifacts."""
  items = [name_or_list] if isinstance(name_or_list, str) else name_or_list
  for item in items:
    p = os.path.abspath(item)
    if os.path.isdir(p):
      build_dir = os.path.join(p, "build")
      if os.path.isdir(build_dir):
        shutil.rmtree(build_dir)

def _command(name_or_list,cmd):
  #Command().exec()
  #pip_executable = path.stage()/"bin"/"pip3"
  PYTHON = dep.instance("python")
  python_executable = PYTHON.executable
  cmd_prefix = [python_executable,"-m","pip",cmd]

  if cmd == "install":
    _clean_build_dir(name_or_list)

  rval = 0
  if(isinstance(name_or_list,str)):
    r = Command(cmd_prefix+[name_or_list]).exec()
    rval = r
  elif (isinstance(name_or_list,list)):
    r = Command(cmd_prefix+name_or_list).exec()
    rval = r

  return rval

def install(name_or_list):
  return _command(name_or_list,"install")

def uninstall(name_or_list):
  return _command(name_or_list,"uninstall")
