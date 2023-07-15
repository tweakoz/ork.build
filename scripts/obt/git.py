###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, shutil
import obt.path
from pathlib import PosixPath
from obt.deco import Deco
from obt.command import run

deco = Deco()

###############################################################################
# Checkout and/or update to a specific branch
#  TODO - handle local changes and other exceptions correctly
###############################################################################

def checkout_update(dest_path,rev,origin="origin"):
    cwd = os.getcwd()
    OK = False
    try:
      os.chdir(dest_path)
      retc = run(["git","checkout",rev],do_log=True)
      retc = run(["git","pull",origin, rev],do_log=True)
      OK = (0 == retc)
    finally:
      os.chdir(cwd)
    return OK

###############################################################################

def Clone(url,
          dest,
          rev="master",
          recursive=False,
          cache=True,
          shallow=False):

  cwd = os.getcwd()
  rval = False
  retc = 0

  dest_path = PosixPath(dest)
  dest_name = dest_path.name
  cache_dest = obt.path.gitcache()/dest_name

  ##############################################################################

  def _checkoutrevandupdate():
    nonlocal cwd
    nonlocal retc
    nonlocal rev
    nonlocal dest_path
    nonlocal recursive
    OK = (0 == retc)
    #print("OK1<%s> retc<%s>"%(OK,retc))
    try:
      os.chdir(dest_path)
      if OK:
        retc = run(["git","checkout",rev],do_log=True)
        OK = (0 == retc)
        #print("OK2<%d>"%OK)
        if OK:
          if recursive:
            retc = run(["git","submodule","update","--init","--recursive"],do_log=True)
            OK = (0 == retc)
            #print("OK3<%d>"%OK)
    finally:
      os.chdir(cwd)
    return OK

  ##############################################################################
  if recursive and (cache==False):
  ##############################################################################

    print("Cloning1 (recursive) URL<%s> to dest<%s>"%(deco.path(url),deco.path(dest_path)))
    retc = run(["git",
                "clone",
                "-n",
                str(url),
                str(dest_path),
                "--recursive"])

    return _checkoutrevandupdate()

  ##############################################################################
  elif cache:
  ##############################################################################

    destpar = (dest_path/"..").resolve()
    print(destpar)
    if False==cache_dest.exists():
      print("Mirroring URL<%s> to dest<%s>"%(deco.path(url),deco.path(cache_dest)))
      retc = run(["git",
                  "clone",
                  str(url),
                  str(cache_dest),
                  "--mirror"])
    print("Cloning2 (from gitcache<%s>) to dest<%s> retc<%s>"%(deco.path(cache_dest),deco.path(dest),retc))
    if dest_path.exists():
      shutil.rmtree(str(dest_path))
    if 0 == retc:
      retc = run(["git",
                  "clone",
                  "--reference",
                  str(cache_dest),
                  str(url),
                  str(dest_path)])
      return _checkoutrevandupdate()

  ##############################################################################
  else:
  ##############################################################################

    print("Cloning3 URL<%s> to dest<%s>"%(deco.path(url),deco.path(dest_path)))
    print("shallow<%d>"%shallow)
    if shallow:
      # shallow clone of speciific rev
      if dest_path.exists():
        shutil.rmtree(str(dest_path))
      run(["mkdir","-p",dest_path])
      curdir = os.getcwd()
      os.chdir(dest_path)
      ####################
      retc = run(["git","init"],do_log=True)
      ####################
      if retc==0:
        retc = run(["git","remote","add","origin",url],do_log=True)
      ####################
      if retc==0:
        retc = run(["git","fetch","--depth","1","origin",rev],do_log=True)
      ####################
      if retc==0:
        retc = run(["git","checkout","FETCH_HEAD"],do_log=True)
      ####################
      if retc==0:
        munged_branch_name = rev
        if munged_branch_name.find("obt-")==-1:
           munged_branch_name = "obt-%s"%rev
        retc = run(["git","checkout","-b",munged_branch_name],do_log=True)
      ####################
      if retc==0:
        os.chdir(curdir)
      ####################
      if retc==0 and recursive:
         retc = run(["git","submodule","update","--init","--recursive"],do_log=True)
      ####################
      print(retc)
      return (0 == retc)
    else:
        retc = run(["git","clone",url,dest_path],do_log=True)
        if 0 == retc:
          return _checkoutrevandupdate()

  ##############################################################################
  return False
