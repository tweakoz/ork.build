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

###############################################################################

def check_hash(output_path,desired):
  if output_path.exists():
    the_md5 = hashlib.md5()
    the_md5.update(output_path.read_bytes())
    actual = the_md5.hexdigest()
    if actual==desired:
      return True
    else:
      print("path<%s>"%output_path)
      print("desired<%s>"%desired)
      print("actual<%s>"%actual)
  return False

###############################################################################
# caching download
###############################################################################

def wget(urls=[],
         output_name=None,
         md5val=None):

  assert(obt.path.downloads().exists())
  output_path = obt.path.downloads()/output_name
  hash_ok = False
  if md5val!=None:
    hash_ok = check_hash(output_path,md5val)
    if hash_ok:
      return output_path

  if False==hash_ok:
    dl_succeeded = False
    for url in urls:
      res = Command(["wget",
                     "-O",
                     output_path,
                     #"--show-progress",
                     url]).exec()

      if res==0:
        dl_succeeded = True 
        if md5val != None:
          hash_ok = check_hash(output_path,md5val)
          if False==hash_ok:
            return None
        return output_path

  return None

################################################################################
# batch downloads
################################################################################
def batch_wget(fset):
  for k in fset.keys():
    v = fset[k]
    wget(urls=[k],output_name=v[0],md5val=v[1])
