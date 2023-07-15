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
import obt.env 

###############################################################################

file_path = os.path.realpath(__file__)
this_dir = pathlib.Path(os.path.dirname(file_path))

###############################################################################

def current():
  return os.environ.get("OBT_SUBSPACE")

###############################################################################

def module_class(module_path,subname):
  import obt.module
  the_module = obt.module.instance("sub_"+subname,module_path)
  if the_module != None:
    return the_module.subspaceinfo
  return None 

###############################################################################

def subspace_dirs():
  subspace_dirs_list = list()
  module_dirs_list = os.environ["OBT_MODULES_PATH"].split(":")
  for module_dir in module_dirs_list:
    subspace_path = obt.path.Path(module_dir)/"subspace"
    if subspace_path.exists():
      subspace_dirs_list += [subspace_path]
  return subspace_dirs_list

###############################################################################

def descriptor(subname):
  subspace_dirs_list = subspace_dirs()
  for subspace_dir in subspace_dirs_list:
    try_path = subspace_dir/("%s.py"%subname)
    if try_path.exists():
      return module_class(try_path,subname)()


###############################################################################

def requires(subname,build_opts=[]):
  sub = descriptor(subname)
  if not sub._manifest_path.exists():
    sub.build(build_opts) # todo skip if manifest present
    sub._manifest_path.touch()
  return sub 

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
    subspace_path = obt.path.Path(module_dir)/"subspace"
    if subspace_path.exists():
      path_list = os.listdir(subspace_path)
      for item in path_list:
        module_test_path = subspace_path/item
        has_py_ext = (str(module_test_path).find(".py")>0)
        if module_test_path.exists() and has_py_ext:
          mclass = module_class(module_test_path,item)
          module = mclass()
          if module!=None:
            e = EnumItem(item,module_test_path,module)
            module_dict[item] = e
  return module_dict

def findWithMethod(named):
  e = enumerate()
  rval = {}
  for k in e.keys():
    item = e[k]
    module = item._module
    if module and hasattr(module,named):
      rval[k] = item
  return rval
