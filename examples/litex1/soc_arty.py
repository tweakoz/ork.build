#!/usr/bin/env python3

import ork.path
import ork.litex

arty_cmd = "./arty.py --output-dir %s"%(ork.path.builds()/"artysoc")

ork.litex.run( cpu="lm32",
               platform="arty",
               target="base",
               cmd=arty_cmd )
