###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, shutil
import ork.path
from pathlib import Path
from ork.deco import Deco
from ork.command import Command

deco = Deco()

###############################################################################

def Clone(url,
          dest,
          rev="master",
          recursive=False,
          cache=True):

  rval = False

  dest_path = Path(dest)
  dest_name = dest_path.name
  cache_dest = ork.path.gitcache()/dest_name

  if recursive and (cache==False):

   print("Cloning (recursive) URL<%s> to dest<%s>"%(deco.path(url),deco.path(dest_path)))
   retc = Command(["git",
                  "clone",
                  "-n",
                  str(url),
                  str(dest_path),
                  "--recursive"]).exec()

   if 0 == retc:
     retc = Command(["git","checkout",rev]).exec()
     if 0 == retc and recursive:
       retc = Command(["git","submodule","update"]).exec()
       if 0 == retc:
         return True

  elif cache:
    retc = 0
    if False==cache_dest.exists():
      print("Mirroring URL<%s> to dest<%s>"%(deco.path(url),deco.path(cache_dest)))

      retc = Command(["git",
                      "clone",
                      str(url),
                      str(cache_dest),
                      "--mirror"]).exec()

    print("Cloning (from gitcache<%s>) to dest<%s>"%(deco.path(cache_dest),deco.path(dest)))

    if dest_path.exists():
      shutil.rmtree(str(dest_path))

    if 0 == retc:
      retc = Command(["git",
                      "clone",
                      "--reference",
                      str(cache_dest),
                      str(url),
                      str(dest_path)]).exec()

    if 0 == retc:
      retc = Command(["git","checkout",rev,str(dest_path)]).exec()
    if 0 == retc and recursive:
      retc = Command(["git","submodule","update",str(dest_path)]).exec()

    return retc==0
  else:
    print("Cloning URL<%s> to dest<%s>"%(deco.path(url),deco.path(dest_path)))
    retc = Command(["git",
                    "clone",
                    str(url),
                    str(dest_path)]).exec()

    if 0 == retc:
      retc = Command(["git","checkout",rev,str(dest_path)]).exec()
    if 0 == retc and recursive:
      retc = Command(["git","submodule","update",str(dest_path)]).exec()
    return 0 == retc

  return False
###############################################################################
