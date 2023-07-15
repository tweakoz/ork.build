###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from pathlib import Path
import hashlib
import obt.path
from obt.command import Command
from obt import wget

###############################################################################
# caching download
###############################################################################

def scp( srcpath=None,
         output_name=None,
         md5val=None):

  assert(obt.path.downloads().exists())
  output_path = obt.path.downloads()/output_name
  hash_ok = False
  if md5val!=None:
    hash_ok = wget.check_hash(output_path,md5val)
    if hash_ok:
      return output_path

  if False==hash_ok:
    dl_succeeded = False
    res = Command(["scp",
                   "-C",
                   srcpath,
                   output_path
                   ]).exec()
    if res==0:
      dl_succeeded = True 
      if md5val != None:
        hash_ok = wget.check_hash(output_path,md5val)
        if False==hash_ok:
          return None
      return output_path

  return None

