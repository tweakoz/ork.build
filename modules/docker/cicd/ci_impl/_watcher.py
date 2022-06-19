#!/usr/bin/env python3
import jinja2, git, datetime, os, subprocess, argparse, shlex, logging, sys, threading, time
from http import server
from yarl import URL
from pathlib import Path
import badge, _masterimpl, uuid, urllib
from enum import Enum
from orkbb import Branch, BranchStatus
from copy import deepcopy
################################################################################

SCRIPTDIR=Path(os.path.dirname(os.path.realpath(__file__)))

################################################################################

class RepoWatcher:
  def __init__(self,config,repo_obj):
    self.config = config
    self.repo_obj = repo_obj
    self.commit_list = list()
    self.branch_dict = dict()
    self.GITDIR = config.repobasedir/self.repo_obj.subdir
    self.giturl = URL(repo_obj.giturl)
    self.update_count = 0
    self.watcherlock = threading.Lock()
    print("OUTPUTDIR<%s>"%self.config.outputdir)
    print("self.GITDIR<%s>"%self.GITDIR)
    ################################################################################
    # watcher repo setup
    ################################################################################
    self.watcherlock.acquire(blocking=True)

    print("begin git clone...")
    if self.repo_obj.skipLFS:
      os.environ["GIT_LFS_SKIP_SMUDGE"]="1"
    os.system("git clone --mirror %s %s"%(self.giturl,self.GITDIR))
    print("end git clone...")

    self.gitrepo = git.Repo(self.GITDIR)
    self.watcherlock.release()

  ################################################################################
  #
  ################################################################################

  def get_branch(self,named):
    item = None
    self.watcherlock.acquire(blocking=True)
    #print("repo<%s> brdict<%s>"%(self.repo_obj.name,self.branch_dict))
    if named in self.branch_dict:
      item = self.branch_dict[named]
    self.watcherlock.release()
    return item

  ################################################################################
  #
  ################################################################################

  def _extract_commit(self,commit):
    sha = commit.hexsha
    email = commit.committer.email
    date = datetime.datetime.fromtimestamp(commit.committed_date)
    return {
      "sha": sha,
      "author": email,
      "date": date,
      "commitpage": self.giturl/"commit"/sha }

  ################################################################################
  def getBranch(self,named):
    branch = None
    self.watcherlock.acquire(blocking=True)
    if named in self.branch_dict:
      branch = self.branch_dict[named]
    self.watcherlock.release()
    return branch
  ################################################################################
  # enumerate commits
  # enumerate branches
  ################################################################################
  def update_branch_info(self):
    self.watcherlock.acquire(blocking=True)
    first_update = (self.update_count==0)
    ##########################################
    #print("begin refetch (self.update_count<%d>)...."%self.update_count)
    for remote in self.gitrepo.remotes:
      remote.fetch()
    #print("end refetch....")
    ##########################################
    self.commit_list.clear()
    ##########################################
    #print("begin parse commits....")
    raw_commit_list = self.gitrepo.iter_commits('--all', max_count=10)
    for commit in raw_commit_list:
      item = self._extract_commit(commit)
      self.commit_list += [ item ]
    #print(self.commit_list)
    #print("end parse commits....")
    ##########################################
    #print("begin branches....")
    for branch_id in self.gitrepo.branches:
      branch_id = branch_id.name
      #print(branch_id)
      ###################################
      # fetch previous, or create new branch_item
      ###################################
      if branch_id in self.branch_dict.keys():
        branch_item = self.branch_dict[branch_id]
        #branch_item["prev_status"] = branch_item["status"]
      else:
        branch_item = Branch()
        branch_item.name = branch_id
        branch_item.repo_obj = self.repo_obj
        branch_item.remote_giturl = self.giturl/"tree"/branch_id
        self.branch_dict[branch_id] = branch_item
        #print("add branch id<%s>"%branch_id)
      ###################################
      # update branch_item
      ###################################
      branch_commit_list = list()
      branch_commits = self.gitrepo.iter_commits(max_count=2, rev=branch_id)
      for commit in branch_commits:
        branch_commit_list += [ self._extract_commit(commit) ]
      if len(branch_commit_list)>0:
        sha = (branch_commit_list[0])["sha"]
        branch_item.last_sha = sha
        branch_item.last_author = (branch_commit_list[0])["author"]
        branch_item.last_date = (branch_commit_list[0])["date"]
        branch_item.last_commit_url = self.giturl/"commit"/sha
    #print(self.branch_dict)
    #print("end parse branches....")
    self.update_count += 1
    self.watcherlock.release()

"""
   def __watch_loop(self):
  while True:
   update_branch_info()
   #update_site()
   ######################################
   # refresh branch symlinks
   ######################################
   for key in self.branch_dict.keys():
     branch_item = self.branch_dict[key]
     SHA = branch_item["lastsha"]
     name = branch_item["name"]
     linksrcpath = self.BUILDSBASEDIR/name
     linkdstpath = self.BUILDSBASEDIR/SHA
     os.system("rm -f %s"%linksrcpath)
     os.chdir(self.BUILDSBASEDIR)
     os.system("ln -s %s %s"%(SHA,name.replace("/","_")))
     STDOUTHTML = self.BUILDSBASEDIR/SHA/"stdout.html"
     if False==os.path.exists(STDOUTHTML):
       os.system("touch %s"%STDOUTHTML)
   ######################################
   # refresh builds
   ######################################
   for key in self.branch_dict.keys():
     branch_item = self.branch_dict[key]
     SHA = branch_item["lastsha"]
     ###########################################
     branch_item["status"] = orkbb.BranchStatus.BUILDING
     update_site()
     ###########################################
     print("building branch<%s> @ sha<%s>"%(branch_item["fixed_branch_name"],branch_item["lastsha"]))
     ###################################################
     name = branch_item["name"]
     os.chdir(SCRIPTDIR)
     ###################################################
     update_site()
   ######################################
   # rerun templatng with build status
   ######################################
   #update_site()
   ######################################
   # sleep
   ######################################
   #print("Sleeping for <%d> seconds" % config.sleeptime)
"""
