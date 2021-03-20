###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, inspect, tarfile, shutil
from pathlib import Path
from yarl import URL
import importlib.util
import ork.path, ork.host
from ork.command import Command, run
from ork.deco import Deco
from ork.wget import wget
from ork import pathtools, cmake, make, path, git, host
from ork._dep_impl import downloadAndExtract
from ork._dep_provider import require 

deco = Deco()
###############################################################################

class GitFetcher:
  ###########################################
  def __init__(self,name):
    self._name = name
    self._git_url = ""
    self._revision = ""
    self._recursive = False
    self._cache = True
  ###########################################
  def descriptor(self):
    return "%s (git-%s)" % (self._name,self._revision)
  ###########################################
  def fetch(self,dest):
    return git.Clone(self._git_url,
                     dest,
                     rev=self._revision,
                     recursive=self._recursive,
                     cache=self._cache,
                     shallow=False)
###############################################################################

class GithubFetcher: # github specific git fetcher
  ###########################################
  def __init__(self,
               name=None,
               repospec=None,
               revision="master",
               recursive=False,
               cache=False,
               shallow=True):
    self._name = name
    # todo : allow user control over protocols
    #  since ssh requires key setup..
    self._git_url = "git@github.com:"+repospec
    self._repospec = repospec
    #self._git_url = "http://github.com/"+repospec
    self._revision = revision
    self._recursive = recursive
    self._cache = cache
    self._shallow = shallow
  ###########################################
  def descriptor(self):
    return "%s (git-%s)" % (self._name,self._revision)
  ###########################################
  def fetch(self,dest):
    ####################################################
    # try to use githubs tarball fetch feature
    # when appropriate because its hella faster
    ####################################################
    if True==self._shallow and \
       False==self._recursive:
      curdir = os.getcwd()
      ghbase = URL("https://github.com")
      url = ghbase/self._repospec/"tarball"/self._revision
      outfname = self._repospec+("-%s.tar.gz"%self._revision)
      outfname = outfname.replace("/","_")
      fetched_path = wget([url],outfname,None)
      if dest.exists():
        shutil.rmtree(str(dest))
      run(["mkdir","-p",dest])
      os.chdir(dest)
      require("gnutar") # because not everyone has tar with --strip-components !
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

class SvnFetcher:
  ###########################################
  def __init__(self,name):
    self._name = name
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

class WgetFetcher:
  ###########################################
  def __init__(self,name):
    self._name = name
    self._fname = ""
    self._url = ""
    self._md5 = ""
    self._arcpath = ""
    self._arctype = ""
  ###########################################
  def descriptor(self):
    return "%s (wget: %s)" % (self._name,self._url)
  ###########################################
  def fetch(self,dest):
    from yarl import URL
    url = URL(self._url)
    dest = path.builds()/self._name
    self._arcpath = downloadAndExtract([url],
                                       self._fname,
                                       self._arctype,
                                       self._md5,
                                       dest)
    return self._arcpath!=None
  ###########################################

###############################################################################

class NopFetcher:
  ###########################################
  def __init__(self,name):
    self._name = name
    self._revision = ""
  ###########################################
  def descriptor(self):
    return "%s (%s)" % (self._name,self._revision)
  ###########################################
  def fetch(self,dest):
    return True
  ###########################################
