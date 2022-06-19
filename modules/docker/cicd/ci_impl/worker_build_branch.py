#!/usr/bin/env python3
import os, sys, subprocess, shlex, argparse, json, threading, select, time, logging
from yarl import URL
from pathlib import Path

parser = argparse.ArgumentParser(description='jinja-build')
parser.add_argument('--sha', metavar="sha", required=True )
parser.add_argument('--outputdir', metavar="outputdir", required=True )
parser.add_argument('--command', metavar="command", required=True, action='append' )
parser.add_argument('--workingdir', metavar="workingdir", required=True )
parser.add_argument("--verbose",action="store_true")

args = vars(parser.parse_args())

SCRIPTDIR=Path(os.path.dirname(os.path.realpath(__file__)))

################################################################################

OUTPUTDIR = Path(args["outputdir"]).absolute()
COMMANDS = args["command"]
WORKINGDIR = args["workingdir"]
REPOBASEDIR = OUTPUTDIR/"repo"
VERBOSE=args["verbose"]
SHA=args["sha"]

#########################################

BASEDIR=OUTPUTDIR/"builds"/SHA
REPODIR=OUTPUTDIR/"repo"
STAGE=BASEDIR/".stage"
LOGTEXTPATH=BASEDIR/"stdout.log"

print("SCRIPTDIR=%s"%SCRIPTDIR)
print("BASEDIR=%s"%BASEDIR)
print("SHA=%s"%SHA)
print("REPODIR=%s"%REPODIR)
print("STAGE=%s"%STAGE)
print("LOGTEXTPATH=%s"%LOGTEXTPATH)
print("COMMANDS<%s>"%COMMANDS)
#########################################
def dirsubst(inpstr):
  outstr = inpstr.replace("$STAGE",str(STAGE))
  outstr = outstr.replace("$REPODIR",str(REPODIR))
  return outstr
#########################################
os.system("mkdir -p %s"%BASEDIR)
os.system("rm -rf %s"%STAGE)
#########################################
WORKINGDIR = dirsubst(WORKINGDIR)

#########################################
# VERBOSE
#########################################

def VERBOSE_RUN(logfile,arg_list):
  logging.basicConfig(stream=sys.stdout,level=logging.INFO)
  logging.addLevelName(logging.INFO+2,'STDERR')
  logging.addLevelName(logging.INFO+1,'STDOUT')
  logger = logging.getLogger("JOB")
  print("VERBOSE run of %s"%cmdlist)
  os.chdir(WORKINGDIR)
  #######################################
  def logstream(stream,loggercb):
    loggercb("Running Job for Sha<%s>"%SHA)
    while True:
      out = stream.readline().decode("UTF-8")
      if out:
        loggercb(out.rstrip())
        try:
          logfile.write(out)
        except:
          pass
      else:
        break
  #######################################
  proc = subprocess.Popen(arg_list,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  stdout_thread = threading.Thread(target=logstream,args=(proc.stdout,lambda s: logger.log(logging.INFO+1,s)))
  stderr_thread = threading.Thread(target=logstream,args=(proc.stderr,lambda s: logger.log(logging.INFO+2,s)))
  stdout_thread.start()
  stderr_thread.start()
  while stdout_thread.isAlive() and stderr_thread.isAlive():
    pass
  #######################################
  proc.wait()
  return proc.returncode 

#########################################
# QUIET
#########################################

def QUIET_RUN(logfile,arg_list):
  print("QUIET run of %s"%arg_list)
  class my_buffer(object):
    def __init__(self, fileobject, prefix):
      self._fileobject = fileobject
      self.prefix = prefix
    def fileno(self):
      return self._fileobject.fileno()
    def write(self, text):
      return self._fileobject.write('%s %s' % (self.prefix, text))
  my_out = my_buffer(logfile, '')
  my_err = my_buffer(logfile, '')
  os.chdir(WORKINGDIR)
  proc = subprocess.Popen(arg_list, stdout=my_out, stderr=my_err)
  proc.wait()
  return proc.returncode 

#########################################


with open(LOGTEXTPATH,"w") as logfile:
  for item in COMMANDS:
    COMMAND = dirsubst(item)
    #########################################
    print("Building Environment for sha<%s>"%SHA)
    arg_list = shlex.split(COMMAND)
    print(arg_list)
    os.environ["USER"] = "builder"
    executor = VERBOSE_RUN if VERBOSE else QUIET_RUN
    retcode = executor(logfile,arg_list)
    if retcode!=0:
      sys.exit(retcode)
  sys.exit(0)