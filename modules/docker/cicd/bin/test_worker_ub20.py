#!/usr/bin/env python3

import os, sys, subprocess, pathlib
import ci_common

########################################################

this_dir = os.path.dirname(os.path.realpath(__file__))
this_dir = pathlib.Path(os.path.abspath(this_dir))

orkid_dir = None
if "ORKID_WORKSPACE_DIR" in os.environ:
  orkid_dir = pathlib.Path(os.environ["ORKID_WORKSPACE_DIR"])

########################################################
# we need an ssh key for the worker to git clone with
#  use a CICD key, not your personal key, as it could
#  be exposed by the build of products
########################################################

secrets_dir = os.environ["SECRETSDIR"]
private_key = secrets_dir/"buildkey.rsa"
public_key = secrets_dir/"buildkey.rsa.pub"

########################################################

cmdlist = list()

cmdlist += ["docker","run"]

cmdlist += ['-v',"%s:/home/workerub20/.ssh/id_rsa:ro"%str(private_key)]
cmdlist += ['-v',"%s:/home/workerub20/.ssh/id_rsa.pub:ro"%str(public_key)]

if orkid_dir!=None:
  cmdlist += ['-v',"%s:/home/workerub20/orkid"%str(orkid_dir)]

cmdlist += ['-it','obtcicd/worker_focal','/bin/bash']

########################################################

ci_common.sync_subprocess(cmdlist)
