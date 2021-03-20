###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, inspect, tarfile
from pathlib import Path
import importlib.util
import ork.path, ork.host
from ork.command import Command, run
from ork.deco import Deco
from ork.wget import wget
from ork import pathtools, cmake, make, path, git, host
from ork import _dep_node
deco = Deco()
###############################################################################
def _get_instance(item):
  if(isinstance(item,str)):
    node = _dep_node.DepNode(item)
    return node.instance
  elif (isinstance(item,_dep_node.DepNode)):
    return item.instance
  #elif (isinstance(item,Provider)):
  #return item
  else:
    assert(False)
###############################################################################
def instance(name):
  return _get_instance(name)
###############################################################################
def _get_node(item):
  if(isinstance(item,str)):
    node = _dep_node.DepNode(item)
    return node
  elif (isinstance(item,_dep_node.DepNode)):
    return item
  else:
    assert(False)
###############################################################################

def switch(linux=None,macos=None):
  if host.IsOsx:
    if macos==None:
      assert(False) # dep not supported on platform
    return macos
  elif host.IsIx:
    if linux==None:
      assert(False) # dep not supported on platform
    return linux
  else:
   return linux


###############################################################################

def enumerate():
  deps = ork.pathtools.patglob(ork.path.deps(),"*.py")
  depnames = set()
  depnodes = dict()
  for item in deps:
    d = os.path.basename(item)
    d = os.path.splitext(d)[0]
    depnames.add(d)
    #print(d)
    dn = ork.dep.DepNode(d)
    if dn:
        depnodes[d] = dn
  return depnodes

###############################################################################

def enumerate_with_method(named):
  depnodes = enumerate()
  rval = {}
  for depitemk in depnodes:
    depitem = depnodes[depitemk]
    if hasattr(depitem,"instance"):
      if hasattr(depitem.instance,named):
        rval[depitemk] = depitem.instance
  return rval

###############################################################################

def downloadAndExtract(urls,
                       outname,
                       archive_type,
                       md5val,
                       build_dest):

  arcpath = wget( urls = urls,
                  output_name = outname,
                  md5val = md5val )


  if arcpath:
    if build_dest.exists():
      Command(["rm","-rf",build_dest]).exec()
    print("extracting<%s> to build_dest<%s>"%(deco.path(arcpath),deco.path(build_dest)))
    print(archive_type)
    build_dest.mkdir()
    if( archive_type=="zip" ):
        os.chdir(str(build_dest))
        Command(["unzip",arcpath]).exec()
    elif archive_type=="tgz":
        os.chdir(str(build_dest))
        Command(["tar","xvf",arcpath]).exec()
    else:
        assert(tarfile.is_tarfile(str(arcpath)))
        tf = tarfile.open(str(arcpath),mode='r:%s'%archive_type)
        tf.extractall(path=str(build_dest))

  return arcpath
