###############################################################################
# Orkid Build System
# Copyright 2010-2022, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import platform, os, pathlib,sys
import multiprocessing
import importlib.util
import obt.path 
import obt.host 

###############################################################################

def instance(identifier,module_path):
  the_module = None
  spec = importlib.util.spec_from_file_location(identifier, str(module_path))
  module_inst = importlib.util.module_from_spec(spec)
  sys.modules[identifier] = module_inst
  a = spec.loader.exec_module(module_inst)
  return module_inst

###############################################################################

def enumerate_simple(enuminterface):
  #######################################
  class EnumItem:
    def __init__(self,name,fullpath,module):
      self._name = name 
      self._fullpath = fullpath
      self._module = module
  #######################################
  hostident = obt.host.description().identifier
  #######################################
  module_dict = dict()
  module_dirs_list = os.environ["OBT_MODULES_PATH"].split(":")
  subdir = enuminterface.subdir
  for module_dir in module_dirs_list:
    module_dir_2 = obt.path.Path(module_dir)/subdir
    if module_dir_2.exists():
      #print(module_dir_2)
      path_list = os.listdir(module_dir_2)
      #print(path_list)
      for item in path_list:
        if item != "__pycache__":
          module_test_path = module_dir_2/item
          #print(item, module_test_path)
          if module_test_path.exists():
            module = enuminterface.tryAsModule(hostident,item,module_test_path)
            if module != None:
              e = EnumItem(item,module_test_path,module)
              module_dict[item] = e
  return module_dict