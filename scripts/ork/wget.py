###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from pathlib import Path
import hashlib 
import ork.path
from ork.command import Command

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

  assert(ork.path.downloads().exists())
  output_path = ork.path.downloads()/output_name

  hash_ok = check_hash(output_path,md5val)

  if False==hash_ok:
    for url in urls:
      res = Command(["wget",
                     "-O",
                     output_path,
                     "--show-progress",
                     url]).exec()

      hash_ok = check_hash(output_path,md5val)
      if False==hash_ok:
        return None
  
  return output_path