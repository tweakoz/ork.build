###############################################################################
# Orkid Build System
# Copyright 2010-2022, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import platform, os, pathlib,sys
from enum import Enum
import obt.path 
import obt.command 

###############################################################################

file_path = os.path.realpath(__file__)
this_dir = pathlib.Path(os.path.dirname(file_path))

###############################################################################
class Type(Enum):
  SINGLE = 1 # loose docker container
  COMPOSITE = 2  # compose based container set

###############################################################################

def module_class(module_path,dokname):
  import obt.module
  the_module = obt.module.instance("dok_"+dokname,module_path)
  if the_module != None:
    return the_module.dockerinfo
  return None 

###############################################################################

def docker_dirs():
  docker_dirs_list = list()
  module_dirs_list = os.environ["OBT_MODULES_PATH"].split(":")
  for module_dir in module_dirs_list:
    docker_path = obt.path.Path(module_dir)/"docker"
    if docker_path.exists():
      docker_dirs_list += [docker_path]
  return docker_dirs_list

###############################################################################

def descriptor(dokname):
  docker_dirs_list = docker_dirs()
  for docker_dir in docker_dirs_list:
    try_path = docker_dir/dokname
    if try_path.exists():
      try_path2 = try_path/("%s.py"%dokname)
      if try_path2.exists():
        return module_class(try_path2,dokname)()

###############################################################################

def enumerate():
  #######################################
  class EnumItem:
    def __init__(self,name,fullpath,module):
      self._name = name 
      self._fullpath = fullpath
      self._module = module
  #######################################
  module_dict = dict()
  module_dirs_list = os.environ["OBT_MODULES_PATH"].split(":")
  for module_dir in module_dirs_list:
    #print(dep_repo)
    docker_path = obt.path.Path(module_dir)/"docker"
    if docker_path.exists():
      path_list = os.listdir(docker_path)
      for item in path_list:
        module_test_path = docker_path/item/("%s.py"%item)
        if module_test_path.exists():
          mclass = module_class(module_test_path,item)
          module = mclass()
          if module!=None:
            e = EnumItem(item,module_test_path,module)
            module_dict[item] = e
  return module_dict

###############################################################################

def enumerate_all_images():
  cmdlist = ["docker","images","-aq"]
  cmd = obt.command.Command(cmdlist)
  as_str = cmd.capture()
  as_list = as_str.split("\n")
  # remove empty items
  as_list = [ x for x in as_list if x ]
  return as_list

def enumerate_all_continaers():
  cmdlist = ["docker","ps","-aq"]
  cmd = obt.command.Command(cmdlist)
  as_str = cmd.capture()
  as_list = as_str.split("\n")
  as_list = [ x for x in as_list if x ]
  return as_list
