#!/usr/bin/env python3

import os, sys, subprocess, pathlib
import ci_common

########################################################

this_dir = os.path.dirname(os.path.realpath(__file__))
this_dir = pathlib.Path(os.path.abspath(this_dir))
orkidci_dir = this_dir/".."

########################################################
# we need an ssh key for the worker to git clone with
#  use a CICD key with read only access, not your personal key
# as it could be exposed by the build of products
########################################################

secrets_dir = os.environ["SECRETSDIR"]
private_key = secrets_dir/"buildkey.rsa"
public_key = secrets_dir/"buildkey.rsa.pub"

andtest_dir = orkidci_dir/"tests"/"android"

########################################################

cmdlist = list()

cmdlist += ["docker","run"]
cmdlist += ['-v',"%s:/home/android/.ssh/id_rsa:ro"%str(private_key)]
cmdlist += ['-v',"%s:/home/android/.ssh/id_rsa.pub:ro"%str(public_key)]
cmdlist += ['-v',"%s:/home/android/android_test:rw"%str(andtest_dir)]
cmdlist += ['-it','obtcicd/worker_android','/bin/bash']

########################################################

ci_common.sync_subprocess(cmdlist)
