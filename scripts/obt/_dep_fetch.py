###############################################################################
# Orkid Build System
# Copyright 2010-2022, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, inspect, tarfile, shutil,sys
from pathlib import Path
from yarl import URL
import importlib.util
import obt.path, obt.host
from obt import patch
from obt.command import Command, run
from obt.deco import Deco
from obt.wget import wget
from obt import pathtools, cmake, make, path, git, host, _globals, buildtrace
from obt._dep_dl import downloadAndExtract
from obt._dep_impl import require 

deco = Deco()

###############################################################################

class Fetcher:
  def __init__(self,name):
    self._name = name
    self._debug = False
    self._patchdict = dict()
  def patch(self):
    for filepath in self._patchdict:
      item_dict = self._patchdict[filepath]
      patch.patch_with_dict(filepath,item_dict)

###############################################################################

class MultiFetcher(Fetcher):
  def __init__(self,name):
    super().__init__(name)
  ###########################################
  def addSubFetcher(self,name):
    pass
  ###########################################
  def fetch(self,dest):
    pass

###############################################################################

class GitFetcher(Fetcher):
  ###########################################
  def __init__(self,name):
    super().__init__(name)
    self._git_url = ""
    self._revision = ""
    self._recursive = False
    self._cache = True
  ###########################################
  def descriptor(self):
    return "%s (git-%s)" % (self._name,self._revision)
  ###########################################
  def fetch(self,dest):
    with buildtrace.NestedBuildTrace({ 
      "op": "fetch(git)",
      "url": self._git_url,
      "rev": self._revision,
      "dest": dest, 
      "recursive": self._recursive, 
      "cache": self._cache,
      "shallow": False }) as nested:
        return git.Clone(self._git_url,
                         dest,
                         rev=self._revision,
                         recursive=self._recursive,
                         cache=self._cache,
                         shallow=False)
###############################################################################

class GithubFetcher(Fetcher): # github specific git fetcher
  ###########################################
  def __init__(self,
               name=None,
               repospec=None,
               revision="master",
               recursive=False,
               cache=False,
               md5val=None,
               shallow=True,
               disable_tarball=False,
               patchdict=dict()):
    super().__init__(name)
    # todo : allow user control over protocols
    #  since ssh requires key setup..
    self._git_url = "git@github.com:"+repospec
    self._repospec = repospec
    #self._git_url = "http://github.com/"+repospec
    self._revision = revision
    self._recursive = recursive
    self._cache = cache
    self._shallow = shallow
    self._md5val = md5val
    self._force_clone = False
    self._disable_tarball = not (self._shallow and (not self._recursive) and (not self._force_clone))
    if disable_tarball:
      self._disable_tarball = True
    self._patchdict = patchdict
    #print(self._git_url)
  ###########################################
  def descriptor(self):
    return "%s (git-%s)" % (self._name,self._revision)
  ###########################################
  def update(self,dest):
    print(self._disable_tarball)
    if self._disable_tarball:
      return git.checkout_update(dest,self._revision)
    else:
      return False
  ###########################################
  def fetch(self,dest):
    ####################################################
    # try to use githubs tarball fetch feature
    # when appropriate because its hella faster
    ####################################################
    #print("UseTarball<%s>"%use_tarball)
    #print(_globals.getOptions())

    use_tarball = not self._disable_tarball

    with buildtrace.NestedBuildTrace({ "op": "fetch(github)", "repospec": self._repospec, "use_tarball": use_tarball, "recursive": self._recursive, "revision": self._revision }) as nested:

      if "usegitclone" in _globals.getOptions():
       if _globals.getOptions()["usegitclone"]==True:
         use_tarball = False
   
      if self._debug:
        print(deco.bright("GithubFetcher<%s> use_tarball<%s>"%(self._name,use_tarball)))

      ####################################################
      if use_tarball:
      ####################################################
        curdir = os.getcwd()
        ghbase = URL("https://github.com")
        url = ghbase/self._repospec/"tarball"/self._revision
        print("URL: %s"%url)
        outfname = self._repospec+("-%s.tar.gz"%self._revision)
        outfname = outfname.replace("/","_")
        fetched_path = wget(urls=[url],output_name=outfname,md5val=self._md5val)
        if fetched_path==None:
          print(deco.red("url<%s> not fetched!"%url))
          return False
        print("dest: %s"%dest)
        print("dest fetched_path: %s"%fetched_path)
        if dest.exists():
          shutil.rmtree(str(dest))
        run(["mkdir","-p",dest])
        os.chdir(dest)
        retc = run(["tar","xvf",fetched_path,"--strip-components","1"])
        os.chdir(curdir)
        return retc==0
      ####################################################
      else: # tried and true way
      ####################################################
        return git.Clone(self._git_url,
                         dest,
                         rev=self._revision,
                         recursive=self._recursive,
                         cache=self._cache,
                         shallow=self._shallow)

###############################################################################

class SvnFetcher(Fetcher):
  ###########################################
  def __init__(self,name):
    super().__init__(name)
    self._url = ""
    self._revision = ""
    self._recursive = False
    self._cache = True
  ###########################################
  def descriptor(self):
    return "%s (svn-%s)" % (self._name,self._revision)
  ###########################################
  def fetch(self,dest):
    url = self._url+"/"+self._revision
    cmd = ["svn","checkout", url, dest]
    retc = run(cmd)
    return retc==0
  ###########################################

###############################################################################

class WgetFetcher(Fetcher):
  ###########################################
  def __init__(self,name):
    super().__init__(name)
    self._fname = ""
    self._url = ""
    self._md5 = ""
    self._arcpath = ""
    self._arctype = ""
    self._dest = path.builds()/self._name
    self._arc_options = []
  ###########################################
  def descriptor(self):
    return "%s (wget: %s)" % (self._name,self._url)
  ###########################################
  def fetch(self,dest):
    from yarl import URL
    url = URL(self._url)
    with buildtrace.NestedBuildTrace({ "op": "fetch(wget)", "url": url, "md5": self._md5, "dest": self._dest, "fname": self._fname, "arctype": self._arctype }) as nested:
      self._arcpath = downloadAndExtract([url],
                                         self._fname,
                                         self._arctype,
                                         self._md5,
                                         self._dest,
                                         arc_options=self._arc_options)
      return self._arcpath!=None

  ###########################################

###############################################################################

class NopFetcher(Fetcher):
  ###########################################
  def __init__(self,name):
    super().__init__(name)
    self._revision = ""
  ###########################################
  def descriptor(self):
    return "%s (%s)" % (self._name,self._revision)
  ###########################################
  def fetch(self,dest):
    return True
  ###########################################
