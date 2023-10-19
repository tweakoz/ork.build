#!/usr/bin/env python3 

import os, ci_common, argparse
from obt import path 

os.environ["DOCKER_BUILDKIT"]="1"

parser = argparse.ArgumentParser(description='obt.build CICD master image builder')
parser.add_argument('--secretsdir', help='ssh key path' )

_args = vars(parser.parse_args())


if "SECRETSDIR" in os.environ:
  secrets_dir = path.Path(os.environ["SECRETSDIR"])
if "secretsdir" in _args:
  secrets_dir = path.Path(_args["secretsdir"])


assert(secrets_dir/"buildkey.rsa.pub").exists()

cmdlist = list()
cmdlist += ["docker","build"]
cmdlist += ["-f", "master.dockerfile"]
cmdlist += ["-t", "obtcicd/master_focal"]
cmdlist += ["--secret", "id=ssh_public,src=%s/buildkey.rsa.pub"%secrets_dir]
cmdlist += ["--secret", "id=ssh_private,src=%s/buildkey.rsa"%secrets_dir]
cmdlist += ["."]

ci_common.sync_subprocess(cmdlist)

