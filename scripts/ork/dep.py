###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, inspect
from pathlib import Path
import importlib.util
import ork.path
  
###############################################################################

class Provider:
	"""base class for all dependency providers"""
	def __init__(self,options={}):
		self.options = options
		pass
	def exists(self):
		return False

###############################################################################

class DepNode:
	"""dependency provider node"""
	def __init__(self,name=None,options={}):
	  assert(isinstance(name,str))
	  self.name = name
	  self.scrname = ("%s.py"%name)
	  self.module_path = ork.path.deps()/self.scrname
	  self.module_spec = importlib.util.spec_from_file_location(self.name, str(self.module_path))
	  self.module = importlib.util.module_from_spec(self.module_spec)
	  self.module_spec.loader.exec_module(self.module)
	  assert(hasattr(self.module,name))
	  self.module_class = getattr(self.module,name)
	  assert(inspect.isclass(self.module_class))
	  assert(issubclass(self.module_class,Provider))
	  self.instance = self.module_class(options=options)
	  print(self.instance)
	  if( False == self.instance.exists() ):
	  	provide = self.instance.provide()
	  	assert(provide==True)

###############################################################################

def require(name,options={}):
	return DepNode(name,options=options)

###############################################################################
