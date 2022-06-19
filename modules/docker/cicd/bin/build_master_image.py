#!/usr/bin/env python3 

import os, ci_common 

os.environ["DOCKER_BUILDKIT"]="1"

cmdlist = list()

secrets_dir = os.environ["SECRETSDIR"]

cmdlist += ["docker","build"]
cmdlist += ["-f", "master.dockerfile"]
cmdlist += ["-t", "obtcicd/master_focal"]
cmdlist += ["--secret", "id=ssh_public,src=%s/buildkey.rsa.pub"%secrets_dir]
cmdlist += ["--secret", "id=ssh_private,src=%s/buildkey.rsa"%secrets_dir]
cmdlist += ["."]

ci_common.sync_subprocess(cmdlist)

