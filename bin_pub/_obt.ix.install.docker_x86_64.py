#!/usr/bin/env python3

###############################################################################
# Orkid Build System
# Copyright 2010-2022, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

###########################################

import pathlib, os, sys, getpass

###########################################
# setup sys.path so we can import _obt_config
###########################################

Path = pathlib.Path
curwd = Path(os.getcwd())
file_path = os.path.realpath(__file__)
file_dir = os.path.dirname(file_path)
sys.path.append(str(file_dir))

###########################################
# minimal (stageless) OBT support for non-environment shell
###########################################

from _obt_config import configFromCommandLine
obt_config = configFromCommandLine()
from obt import path, pathtools, env, command, deco, wget
deco = deco.Deco()

###########################################
UID = os.getuid()
USERNAME = getpass.getuser()

print(deco.cyan("installing uidmap"))
command.run(["sudo","apt","install","uidmap", "dbus-user-session"],do_log=True)

#disable system scoped docker daemon
print(deco.cyan("disabling system scoped docker"))
command.run(["sudo","systemctl","disable","--now","docker.service","docker.socket"],do_log=True)
command.system(["curl","-fsSL","https://get.docker.com/rootless","|","sh"],do_log=True)
print(deco.cyan("docker installed!"))

print(deco.cyan("allowing rootless docker to run when logged out"))
command.run(["sudo","loginctl","enable-linger",USERNAME],do_log=True)

#!/bin/bash
#
# https://docs.docker.com/build/buildkit/
# https://github.com/docker/buildx/releases/
# https://github.com/docker/buildx

## For Ubuntu 24.04 try: sudo apt install docker-buildx
## Or run the commands below.

VERSION="v0.17.1"
HOMEDIR = path.Path(os.environ["HOME"])
PLUGDIR = HOMEDIR}/".docker"/"cli-plugins"
pathtools.mkdir(f"{PLUGDIR}",parents=True)
wget.wget(urls=["https://github.com/docker/buildx/releases/download/$VERSION/buildx-$VERSION.linux-amd64"],
          output_name = f"{PLUGDIR}/docker-buildx",
          md5val="0")
command.run(["chmod", "+x", f"{PLUGDIR}/docker-buildx"])

print(deco.orange("add the following to your .bashrc:"))
print(deco.yellow("export PATH=%s/bin:$PATH"%HOMEDIR))
print(deco.yellow("export DOCKER_HOST=unix:///run/user/%d/docker.sock"%UID))
print(deco.yellow("export DOCKER_BUILDKIT=1"))
print(deco.yellow("export COMPOSE_DOCKER_CLI_BUILD=1"))

print(deco.yellow("ALSO: see https://docs.docker.com/go/rootless/"))
