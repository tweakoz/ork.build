import sys, threading, time, json, random, os, base64
from pathlib import Path
from yarl import URL
from orkbb import BranchStatus,WorkerStatus, DEBUGFORMAT
import _watcher, _zmqssh,zmq
################################################################################
# MasterConfigWorker
################################################################################
class Worker(object):
  ############################################
  def __init__(self,name,configobj):
    self.name = name
    self.config = configobj
    self.thread = None
    self.variantlist = list()
    self.status = WorkerStatus.INIT
    self.scheduler = None
    self.curvaridx = 0
    self.curvarname = None
    self.curvariant = None
    self.buildstatus = None
    self.connected = False
    self.jobindex = 0
  ############################################
  def start(self,sched):
    self.scheduler = sched
  ############################################
  def curVariant(self):
    varnames = sorted([item.name for item in self.variantlist])
    numvarnames = len(varnames)
    varname = varnames[self.curvaridx]
    vari = self.scheduler.config.variants[varname]
    return vari
  ############################################
  def advanceVariant(self):
    numvarnames = len(self.variantlist)
    self.curvaridx += 1
    if self.curvaridx > (numvarnames-1):
      self.curvaridx = 0
    self.jobindex += 1
  ############################################
  def curRepo(self):
    return self.curVariant().repo
  ############################################
  def curBranch(self):
      vari = self.curVariant()
      repo = self.curRepo()
      repo.watcher.update_branch_info()
      branch_obj = repo.watcher.get_branch(vari.branchname)
      return branch_obj
  ############################################
  def onWaiting(self):
    reply = {"state": "wait"}
    vari = self.curVariant()
    repo = self.curRepo()
    branch_obj = self.curBranch()
    if branch_obj != None:
      reply["jobindex"] = self.jobindex
    return reply
  ############################################
  def onInitializing(self):
    reply = {"state": "wait"}
    vari = self.curVariant()
    repo = self.curRepo()
    branch_obj = self.curBranch()
    if branch_obj != None:
      self.curvarname = vari.name
      self.curvariant = self.scheduler.config.variants[vari.name]
      self.curvariant.prvbuildstatus=self.curvariant.curbuildstatus
      self.curvariant.curbuildstatus = BranchStatus.BUILDING
      self.curvariant.head_sha = branch_obj.last_sha
      self.curvariant.shaurl = branch_obj.last_commit_url
      self.status = WorkerStatus.FETCHING
      reply = {"state": "init"}
      reply["sha"] = branch_obj.last_sha
      reply["variant"] = str(self.curvarname)
      reply["platform"] = vari.platform
      reply["branchname"] = str(vari.branchname)
      self.scheduler.onWorkerStatus(self)
    return reply
  ############################################
  def onFetching(self):
    reply = {"state": "wait"}
    vari = self.curVariant()
    repo = self.curRepo()
    branch_obj = self.curBranch()
    if branch_obj != None:
        reply = {"state": "fetch"}
        reply["variant"] = str(self.curvarname)
        reply["sha"] = branch_obj.last_sha
        reply["repourl"] = str(repo.giturl)
        reply["reponame"] = repo.name
        reply["skipLFS"] = repo.skipLFS
        self.status = WorkerStatus.BUILDING
        self.scheduler.onWorkerStatus(self)
    return reply
  ############################################
  def onBuilding(self):
    reply = {"state": "wait"}
    if self.status == WorkerStatus.BUILDING:
      vari = self.curvariant
      repo = vari.repo
      reply = {"state": "build"}
      reply["workingdir"] = repo.workingdir
      reply["cmd"] = "build"
      reply["commandlist"] = repo.commandlist
      reply["subdir"] = repo.subdir
    return reply
  ############################################
  def onReporting(self,message):
    reply = {"state": "wait"}
    if self.status == WorkerStatus.BUILDING:
      self.curvariant.buildtime = message["buildtime"]
      if message["status"]=="OK":
        self.curvariant.curbuildstatus = BranchStatus.PASSED
      else:
        self.curvariant.curbuildstatus = BranchStatus.FAILED
      #######################
      ba = bytearray(base64.b64decode(message["log_html_enc"]))
      f = open(self.curvariant.log_html, 'wb')
      f.write(ba)
      f.close()
      #######################
      # advance variant on worker
      #######################
      self.curvarname = None
      self.curvariant = None
      self.status = WorkerStatus.WAIT
      self.scheduler.onWorkerStatus(self)
      self.advanceVariant()
      reply = {"state": "report"}
    return reply
  ############################################
  def __repr__(self):
    return str(self.__dict__)
################################################################################
# MasterConfigRepo
################################################################################
class Repo(object):
  ############################################
  def __init__(self,config,repo_key):
    configobj = config.config_dict["repos"][repo_key]
    self.name = repo_key
    self.config = config
    self.giturl = configobj["giturl"]
    self.subdir = configobj["subdir"]
    self.skipLFS = configobj["skipLFS"]
    self.workingdir = configobj["workingdir"]
    self.commandlist = configobj["commandlist"]
    self.enabled = True
    if "enable" in configobj:
      self.enabled = configobj["enable"]
    self.watcher = None
  def poll(self):
    pass
  ############################################
  def startWatcher(self):
    if self.enabled:
      print("INIT REPOOBJ repo_key<%s>"%self.name)
      print("INIT REPOOBJ giturl<%s>"%self.giturl)
      print("INIT REPOOBJ subdir<%s>"%self.subdir)
      self.watcher = _watcher.RepoWatcher(self.config,self)
  ############################################
  def __repr__(self):
    return str(self.__dict__)
################################################################################
# MasterConfigVariant
################################################################################
class Variant(object):
  ############################################
  def __init__(self,configobj,name,outputdir,repo,branchname):
    self.name = name
    self.enabled = True
    self.schedule = configobj["schedule"]
    self.workers = configobj["workers"]
    self.branchname = branchname
    self.platform = configobj["platform"]
    if "enable" in configobj:
      self.enabled = configobj["enable"]
    self.repo = repo
    self.repourl = repo.giturl
    self.outputdir = outputdir/name
    self.outrelpath = Path(name)
    self.index_html= self.outrelpath/"index.html"
    self.log_html = self.outrelpath/"log_stdout.html"
    self.status_svg= self.outrelpath/"status.svg"
    self.curbuildstatus = BranchStatus.INIT
    self.prvbuildstatus = BranchStatus.INIT
    self.branchurl = repo.giturl
    self.buildtime="---"
    self.head_sha="---"
    self.shaurl = "---"
  ############################################
  def updateRepoData(self):
    if self.repo.watcher!=None:
      branch = self.repo.watcher.getBranch(self.branchname)
      if branch!=None:
        self.branchurl = branch.remote_giturl
  ############################################
  def __repr__(self):
    return str(self.__dict__)
################################################################################
# MasterConfig
################################################################################
class Config(object):
  ###################################################################
  def __init__(self,configfile,outputdir):
    PROJTEXT = ""
    self.repos = {}
    self.variants = {}
    self.workers = {}
    self.master_name = "???"
    self.user_branch_list=[]
    self.skipLFS = False
    self.sleeptime = 3600
    self.workingdir= "$REPODIR"
    self.outputdir= outputdir
    self.repobasedir = self.outputdir/"repo"
    self.buildsbasedir = self.outputdir/"builds"
    print("repobasedir<%s>"%self.repobasedir)
    print("self.buildsbasedir<%s>"%self.buildsbasedir)
    print("remove old build")
    os.system("rm -rf %s"%self.repobasedir)
    os.system("mkdir -p %s"%self.repobasedir)
    os.system("mkdir -p %s"%self.buildsbasedir)
    #######################################
    with open(configfile,"r") as f:
      PROJTEXT = f.read()
    self.config_dict = json.loads(PROJTEXT)
    #######################################
    self.master_name = self.config_dict["master_name"]
    self.master_bind_addr = self.config_dict["master_bind_addr"]
    self.master_bind_port = self.config_dict["master_bind_port"]
    self.http_bind_addr = self.config_dict["http_bind_addr"]
    self.http_bind_port = self.config_dict["http_bind_port"]
    #######################################
    for worker_key in self.config_dict["workers"].keys():
      worker = self.config_dict["workers"][worker_key]
      self.workers[worker_key] = Worker(worker_key,worker)
    #######################################
    for repo_key in self.config_dict["repos"].keys():
      self.repos[repo_key] = Repo(self,repo_key)
    #######################################
    for vari_key in self.config_dict["variants"].keys():
      vari = self.config_dict["variants"][vari_key]
      repo = self.repos[vari["repo"]]
      for branch in vari["branches"]:
        qualname = Path(vari_key)/branch
        outdir = outputdir/qualname
        variant = Variant(vari,qualname,outdir,repo,branch)
        if variant.enabled:
          self.variants[qualname] = variant
          for w in variant.workers:
            worker = self.workers[w]
            worker.variantlist += [variant]
  ###################################################################
  def start(self):
    for repo_key in self.config_dict["repos"].keys():
      self.repos[repo_key].startWatcher()
