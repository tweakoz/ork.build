#!/usr/bin/env python3
import jinja2, git, datetime, os, subprocess, argparse, shlex, logging, sys, threading, time
from http import server
from yarl import URL
from pathlib import Path
import badge, uuid, urllib, scheduler, httphandler, orkbb

SCRIPTDIR=Path(os.path.dirname(os.path.realpath(__file__)))

################################################################################

parser = argparse.ArgumentParser(description='orkbb-master')
parser.add_argument('--project', metavar="projectfile", required=True, help='path of json project file' )
parser.add_argument('--outputdir', default=SCRIPTDIR/"output", metavar="outputdir", help='outputdirectory' )
parser.add_argument("--debug",action="store_true")
parser.add_argument("--verbose",action="store_true")
args = vars(parser.parse_args())

################################################################################

VERBOSE=args["verbose"]
OUTPUTDIR = Path(args["outputdir"])
print("remove old outputdir")
os.system("rm -rf %s"%OUTPUTDIR)
os.system("mkdir -p %s"%OUTPUTDIR)

################################################################################
# scheduler
################################################################################

projectpath = Path(args["project"])
sched = scheduler.Scheduler(projectpath,OUTPUTDIR)
#print(SCHED)
http_addr = sched.config.http_bind_addr
http_port = sched.config.http_bind_port
################################################################################
# web server
################################################################################
os.chdir(OUTPUTDIR)
server_address = (http_addr, http_port)
handler = httphandler.HandlerClass(OUTPUTDIR,sched.sitelock)
httpd = server.HTTPServer(server_address, handler)
httpd.serve_forever()
