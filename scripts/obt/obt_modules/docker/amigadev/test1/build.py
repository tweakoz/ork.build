#!/usr/bin/env python3

from ork import path, pathtools, command
import os
from pathlib import Path

this_path = os.path.realpath(__file__)
this_dir = Path(os.path.dirname(this_path))

builddir = path.builds()/"amigadev-test1"
pathtools.mkdir(builddir,clean=True)

command.run([
    "docker", "run",
    "-it",
    "--mount","type=bind,source=%s,target=/home/amigadev/test1,readonly"%this_dir,
    "--mount","type=bind,source=%s,target=/home/amigadev/test1-build"%builddir,
    "obt-amigadev:latest",
    "./test1/_build.sh"])
