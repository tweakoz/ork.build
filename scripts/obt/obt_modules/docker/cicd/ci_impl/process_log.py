#!/usr/bin/env python3
import os, sys, subprocess, shlex, argparse
from pathlib import Path

parser = argparse.ArgumentParser(description='jinja-build')
parser.add_argument('--directory', metavar="directory", required=True, help='directory' )
parser.add_argument('--basedir', metavar="basedir", required=True, help='basedir' )
args = vars(parser.parse_args())


SCRIPTDIR=Path(os.path.dirname(os.path.realpath(__file__)))
DIRECTORY = Path(args["directory"])
BASEDIR = Path(args["basedir"])

#print(SCRIPTDIR)
#########################################
LOGTEXTPATH=DIRECTORY/"stdout.log"
LOGPROC=DIRECTORY/"stdout.proc"
LOGHTML=DIRECTORY/"stdout.html"
#########################################
#print("SHA=%s"%SHA)
#print("SCRIPTDIR=%s"%SCRIPTDIR)
#print("DIRECTORY=%s"%DIRECTORY)
#print("LOGPATH=%s"%LOGPATH)
#print("LOGHTML=%s"%LOGHTML)
LOGTEXT = LOGTEXTPATH.read_text()
#########################################
# redact paths
#########################################
searchstr = str(BASEDIR).replace("/","\/")
replacestr = "[JOBDIR]"
result = str(LOGTEXT).replace(searchstr,replacestr)
#########################################
searchstr = "/home/builder"
replacestr = "[HOMEDIR]"
result = result.replace(searchstr,replacestr)
#########################################
with open(LOGPROC,mode="w") as f:
  f.write(result)
#########################################
cmd = ["aha","--black","--title", "yo", "-f",LOGPROC]
result = subprocess.check_output(cmd,universal_newlines=True)

with open(LOGHTML,mode="w") as f:
  f.write(result)

#
