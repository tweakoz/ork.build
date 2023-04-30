###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from ork import dep, path, command, env
import os 

class Manifest:
  def __init__(self,_name,_path):
    self._name = _name
    self._path = _path
  def exists(self):
    return self._path.exists()
  def touch(self):
    return command.run(["touch",self._path])

def instance(node):
    subspace = os.environ["OBT_SUBSPACE"]
    subspace_dir = path.subspace_dir()
    #print(node._name,subspace,node.allowed_in_subspace(subspace))
    if subspace!="host" and node.allowed_in_subspace(subspace):
      subspace_manifest_dir = subspace_dir/"manifests"
      try_subspace = subspace_manifest_dir/node._name
      return Manifest(node._name,try_subspace)
    else:
      host_manifest_dir = path.stage()/"manifests"
      try_host = host_manifest_dir/node._name
      return Manifest(node._name,try_host)
    
