#!/usr/bin/env python3

import os
from ork import path, deco
from ork.command import Command

deco = deco.Deco()

os.chdir(path.deps())
print(deco.inf("ork.build dependency provider list:"))
os.system("ls *.py | grep --invert-match ^_ | cut -d'.' -f1 | tr '\n' ' '")
print()
