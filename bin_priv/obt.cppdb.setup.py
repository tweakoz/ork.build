#!/usr/bin/env python3 
from obt import command

cmd = ["ork.python","-m","pip"]

command.run(cmd + ["install","tree-sitter==0.21.3"])
command.run(cmd + ["install","tree-sitter-cpp==0.22.3"])
command.run(cmd + ["install","tree-sitter-python==0.23.2"])
command.run(cmd + ["install","tree-sitter-lua==0.2.0"])
command.run(cmd + ["install","tree-sitter-glsl==0.2.0"])
