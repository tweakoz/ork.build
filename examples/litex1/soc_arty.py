#!/usr/bin/env python3

import obt.path
import obt.litex

arty_cmd = "./arty.py --output-dir %s"%(obt.path.builds()/"artysoc")

obt.litex.run( cpu="lm32",
               platform="arty",
               target="base",
               cmd=arty_cmd )
