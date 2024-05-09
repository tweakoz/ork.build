#!/usr/bin/env python3
import os, sys, subprocess, argparse, logging
from yarl import URL
from pathlib import Path

parser = argparse.ArgumentParser(description='jinja-build')
parser.add_argument('--sha', metavar="sha", help='sha',required=True )
parser.add_argument('--outputdir', metavar="outputdir", help='outputdirectory',required=True )
parser.add_argument('--gitURL', metavar="gitURL", required=True )
parser.add_argument("--skipLFS",action="store_true")

args = vars(parser.parse_args())

SCRIPTDIR=Path(os.path.dirname(os.path.realpath(__file__)))

################################################################################

OUTPUTDIR = Path(args["outputdir"])
SKIPLFS = args["skipLFS"]
GITURL = args["gitURL"]
REPOBASEDIR = OUTPUTDIR/"repo"

#########################################

SHA=args["sha"]
BASEDIR=OUTPUTDIR/"builds"/SHA
REPODIR=OUTPUTDIR/"repo"

print("SCRIPTDIR=%s"%SCRIPTDIR)
print("BASEDIR=%s"%BASEDIR)
print("SHA=%s"%SHA)
print("REPODIR=%s"%REPODIR)

#########################################
os.system("mkdir -p %s"%BASEDIR)
os.system("rm -rf %s"%REPODIR)
print("Cloning %s"%GITURL)
if SKIPLFS:
  os.environ["GIT_LFS_SKIP_SMUDGE"]="1"
os.system("git clone --recursive %s %s"%(GITURL,REPODIR))
os.chdir(REPODIR)
os.system("git fetch")
os.system("git checkout %s" % SHA)
os.system("git submodule update")
