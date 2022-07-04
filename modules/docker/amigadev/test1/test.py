#!/usr/bin/env python3

from ork import command, path

builddir = path.builds()/"amigadev-test1"

command.run(["docker",
             "run",
              "--mount",
              "type=bind,source=%s,target=/home/amigadev/test1/.build"%builddir,
             "sebastianbergmann/amitools:latest",
              "vamos", 
              "/home/amigadev/test1/.build/main.exe"
              ])
