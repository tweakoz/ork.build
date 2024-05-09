#!/usr/bin/env python3
import os, subprocess, argparse, time, transitions, base64
from pathlib import Path
import _workerimpl, _zmqssh

SCRIPTDIR=Path(os.path.dirname(os.path.realpath(__file__)))

################################################################################

parser = argparse.ArgumentParser(description='orkbb-worker')
parser.add_argument('--project', metavar="projectfile", required=True, help='path of json project file' )
parser.add_argument('--outputdir', default=SCRIPTDIR/"output", metavar="outputdir", help='outputdirectory' )
parser.add_argument("--debug",action="store_true")
parser.add_argument("--verbose",action="store_true")
args = vars(parser.parse_args())

################################################################################

VERBOSE=args["verbose"]
OUTPUTDIR = Path(args["outputdir"]).absolute()
BASEDIR=OUTPUTDIR/"builds"
print("remove old outputdir<%s>"%OUTPUTDIR)
os.system("rm -rf %s"%OUTPUTDIR)
os.system("mkdir -p %s"%OUTPUTDIR)

################################################################################

config = _workerimpl.Config(Path(args["project"]),OUTPUTDIR)
print(config)

#########################################
def dirsubst(inpstr,REPODIR):
  outstr = inpstr.replace("$REPODIR",str(REPODIR))
  outstr = outstr.replace("$STAGE",str(STAGE))
  return outstr
################################################################################
def tunnelledZMQ():
  global config
  #impl = _zmqssh.ZmqSsh2
  impl = _zmqssh.Direct

  rval = impl(ipaddr=(config.master_ssh_host,config.master_ssh_port),
              user=config.master_ssh_user,
              key="~/.ssh/id_rsa",
              lbindaddr=(config.master_zmq_host, config.master_zmq_port) )
  return rval
#########################################

class Worker(object):
  states = ["booting","connecting","waiting","initializing","fetching","building","reporting"]

  def __init__(self):
    ####################################
    self.name = "worker"
    self.cur_sha = None
    self.cur_outdir = None
    self.buildtime = 0
    self.returncode = 0
    ####################################
    self._fsm = transitions.Machine(model=self,queued=True,states=Worker.states,initial="booting")
    self._fsm.add_transition(trigger='boot', source='booting', dest='connecting')
    self._fsm.add_transition(trigger='advance', source='connecting', dest='waiting')
    self._fsm.add_transition(trigger='advance', source='waiting', dest='initializing')
    self._fsm.add_transition(trigger='advance', source='initializing', dest='fetching')
    self._fsm.add_transition(trigger='advance', source='fetching', dest='building')
    self._fsm.add_transition(trigger='advance', source='building', dest='reporting')
    self._fsm.add_transition(trigger='advance', source='reporting', dest='waiting')
    self._fsm.add_transition('reset', '*', 'waiting')
    ####################################
    self._fsm.on_enter_connecting('beginConnecting')
    self._fsm.on_enter_waiting('beginWaiting')
    self._fsm.on_enter_initializing('beginInitializing')
    self._fsm.on_enter_fetching('beginFetching')
    self._fsm.on_enter_building('beginBuilding')
    self._fsm.on_enter_reporting('beginReporting')
    ####################################

  ####################################
  def sendMessage(self,message):
    reply = None
    with tunnelledZMQ() as socket:
      socket.send_json(message)
      keepwaiting = True
      while keepwaiting:
        qres = socket.recv_json(timeout=5)
        if qres==None:
          print("worker-buildstatus timeout, waiting...")
        else:
          keepwaiting = False
          reply = qres
    return reply
  ####################################
  def beginConnecting(self):
    print("CONNECTING")
    keepconnecting=True
    while keepconnecting:
      reply = self.sendMessage({
        "command": "worker-connect",
        "worker": config.name
      })
      keepconnecting=(reply==None)
  ####################################
  def beginWaiting(self):
    keepwaiting=True
    while keepwaiting:
      reply=self.sendMessage({
        "command": "worker-waiting",
        "worker": config.name
      })
      if reply!=None:
        print("WAIT reply<%s>"%reply)
        assert(reply["state"] == "wait")
        if "jobindex" in reply:
          self.jobindex = reply["jobindex"]
          keepwaiting = False
  ####################################
  def beginInitializing(self):
    message = {"command": "worker-initializing",
               "worker": config.name}
    reply = self.sendMessage(message)
    if reply["state"] != "init":
      self.reset()
      return
    print("INIT<%s>"%reply)
  ####################################
  def beginFetching(self):
    message = {"command": "worker-fetching",
               "worker": config.name}
    reply = self.sendMessage(message)
    print("BEGINFETCH"%reply)
    if reply["state"] != "fetch":
      self.reset()
      return
    variant = reply["variant"]
    os.chdir(SCRIPTDIR)
    self.cur_sha = reply["sha"]
    self.cur_outdir = OUTPUTDIR/variant
    cmdlist = [ "./worker_fetch_branch.py",
                "--sha", self.cur_sha,
                "--gitURL", reply["repourl"],
                "--outputdir", self.cur_outdir,
    ]
    if reply["skipLFS"]:
      cmdlist += ["--skipLFS"]
    proc = subprocess.Popen(cmdlist)
    proc.wait()
    print("ENDFETCH")
  ####################################
  def beginBuilding(self):
    message = {"command": "worker-building",
               "worker": config.name}
    reply = self.sendMessage(message)
    print("BEGINBUILD<%s>"%reply)
    if reply["state"] != "build":
      self.reset()
      return
    os.chdir(SCRIPTDIR)

    print(reply["commandlist"])

    cmdlist = [ "./worker_build_branch.py",
                "--sha", self.cur_sha,
                "--outputdir", self.cur_outdir,
                "--workingdir", reply["workingdir"],
    ]

    for item in reply["commandlist"]:
      cmdlist += ["--command",item]

    print(cmdlist)

    if VERBOSE:
      cmdlist += ["--verbose"]

    time_start = time.time()
    proc = subprocess.Popen(cmdlist)
    proc.wait()
    print("ENDBUILD ret<%d>"%proc.returncode)
    self.returncode = proc.returncode
    time_end = time.time()
    time_diff = time_end-time_start
    self.buildtime = time.strftime('%Hh:%Mm:%Ss', time.gmtime(time_diff))
  ####################################
  def beginReporting(self):
    print("REPORT")
    build_dir = self.cur_outdir/"builds"/self.cur_sha
    cmdlist = [ "./process_log.py",
                "--basedir", self.cur_outdir,
                "--directory", build_dir
              ]
    proc = subprocess.Popen(cmdlist)
    proc.wait()
    log_html_path = build_dir/"stdout.html"
    f = open(log_html_path,'rb')
    bytes = bytearray(f.read())
    log_html_enc = base64.b64encode(bytes).decode("utf-8")
    f.close()
    message = {"command": "worker-reporting",
               "worker": config.name,
               "buildtime": self.buildtime,
               "log_html_enc": log_html_enc }
    if self.returncode==0:
      message["status"] = "OK"
    else:
      message["status"] = "ERROR"
    reply = self.sendMessage(message)
    os.system("rm -rf %s"%self.cur_outdir)
    if reply["state"] != "report":
      self.reset()
      return
    time.sleep(config.sleeptime)
  ####################################

################################################################################

worker = Worker()
worker.boot()

################################################################################
# Main Loop
################################################################################

while True:
  worker.advance()
