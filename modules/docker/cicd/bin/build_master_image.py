#!/usr/bin/env python3 

import os, ci_common, argparse
from obt import path, deco
deco = deco.Deco()

os.environ["DOCKER_BUILDKIT"]="1"

parser = argparse.ArgumentParser(description='obt.build CICD master image builder')
parser.add_argument('--secretsdir', help='ssh key path' )

_args = vars(parser.parse_args())

have_secrets = False
if "SECRETSDIR" in os.environ:
  secrets_dir = path.Path(os.environ["SECRETSDIR"])
  have_secrets = True
if "secretsdir" in _args and _args["secretsdir"]!=None:
  secrets_dir = path.Path(_args["secretsdir"])
  have_secrets = True

if not have_secrets:
  print(deco.err("##########################################################"))
  print()
  print(deco.err(parser.format_usage()))
  print(deco.err("##########################################################"))
  assert(False)


assert(secrets_dir/"buildkey.rsa.pub").exists()

cmdlist = list()
cmdlist += ["docker","build"]
cmdlist += ["-f", "master.dockerfile"]
cmdlist += ["-t", "obtcicd/master_focal"]
cmdlist += ["--secret", "id=ssh_public,src=%s/buildkey.rsa.pub"%secrets_dir]
cmdlist += ["--secret", "id=ssh_private,src=%s/buildkey.rsa"%secrets_dir]
cmdlist += ["."]

ci_common.sync_subprocess(cmdlist)

