import json, pprint, ast, json, sys, jsonpickle, threading, time
from pathlib import Path
from yarl import URL
from enum import Enum
pp = pprint.PrettyPrinter(indent=4,depth=4)
jsonpickle.set_preferred_backend('json')
jsonpickle.set_encoder_options('json', sort_keys=True, indent=3)

################################################################################
def DEBUGFORMAT(obj):
  a = jsonpickle.encode(obj,max_depth=2)
  return str(a)

################################################################################
class BranchStatus(Enum):
  INIT = 1
  BUILDING = 2
  PASSED = 3
  FAILED = 4
  WAIT = 5
################################################################################
class WorkerStatus(Enum):
  INIT = 1
  FETCHING = 2
  BUILDING = 3
  WAIT = 4
################################################################################
class Branch:
  def __init__(self):
    self.name = None
    self.repo_obj = None
    self.remote_giturl = None
    self.commits = None
    self.last_sha = None
    self.last_author = None
    self.last_data = None
    self.last_commit_url = None
################################################################################
"""
def update_badge(item):

 ##################################
 # set text
 ##################################

 if item["status"]==BranchStatus.PASSED:
   right_text = "PASSED"
 elif item["status"]==BranchStatus.FAILED:
   right_text = "FAILED"
 elif item["status"]==BranchStatus.INIT:
   right_text = "INIT"
 elif item["status"]==BranchStatus.BUILDING:
   right_text = "BUILDING"
 else:
   right_text = "????"

 ##################################
 # set color
 ##################################

 right_color = "#000000"

 if item["status"]==BranchStatus.PASSED:
   right_color = "#006000"
 elif item["status"]==BranchStatus.FAILED:
   right_color = "#500000"
 elif item["status"]==BranchStatus.INIT:
   right_color = "#000000"
 elif item["status"]==BranchStatus.BUILDING:
   if item["prev_status"]==BranchStatus.PASSED:
     right_color = "#006000"
   elif item["prev_status"]==BranchStatus.FAILED:
     right_color = "#500000"
   elif item["prev_status"]==BranchStatus.INIT:
     right_color = "#404040"

 print("NEWBRANCHSTATUS<%s>"%item["status"])
 ##################################
 # generate badge
 ##################################

 SHA = item["lastsha"]
 shadir = BUILDSBASEDIR/SHA
 os.system("mkdir -p %s"%str(shadir))
 badge.create( outpath=str(shadir/"status.svg"),
               left_text="BranchStatus",right_text=right_text,
               left_color="#202040",right_color=right_color)
"""
