import sys, threading, time, json, random
from pathlib import Path
from yarl import URL
from orkbb import BranchStatus,WorkerStatus, DEBUGFORMAT

################################################################################
# WorkerConfig
################################################################################
class Config(object):
  ###################################################################
  def __init__(self,configfile,outputdir):
    PROJTEXT = ""
    self.outputdir= outputdir
    #######################################
    with open(configfile,"r") as f:
      PROJTEXT = f.read()
    PROJOBJ = json.loads(PROJTEXT)
    #######################################
    self.name = PROJOBJ["name"]
    self.master_ssh_host = PROJOBJ["master_ssh_host"]
    self.master_ssh_user = PROJOBJ["master_ssh_user"]
    self.master_ssh_port = PROJOBJ["master_ssh_port"]
    self.master_zmq_host = PROJOBJ["master_zmq_host"]
    self.master_zmq_port = PROJOBJ["master_zmq_port"]
    self.sleeptime = PROJOBJ["sleeptime"]
    #######################################
  #####
