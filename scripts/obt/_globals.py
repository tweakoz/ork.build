###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

global yo
global _options

yo = "yo"
_options = dict()
_nodes = dict()

###############################################################################

def config():
  return None 

###############################################################################

def setOption(key,value):
  _options[key] = value

###############################################################################

def setOptions(opts):
  _options = opts

###############################################################################

def getOptions():
  return _options

###############################################################################

def getOption(named):
  if named in _options:
    return _options[named]
  else:
   return None 

###############################################################################

def hasOption(named):
  if named in _options:
    return True
  else:
   return False

###############################################################################

def tryBoolOption(named):
  if named in _options:
    return _options[named]
  else:
    return False

###############################################################################

def setNode(named,value):
  _nodes[named] = value

###############################################################################

def getNode(named):
  #print(_nodes)
  if named in _nodes:
    return _nodes[named]
  else:
   return None 

###############################################################################

def enableBuildTracing():
  _options["BUILDTRACE"] = True

###############################################################################

def isBuildTraceEnabled():
  return "BUILDTRACE" in _options
