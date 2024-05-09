#!/usr/bin/env python3
###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import argparse, sys, os
from obt import deco, path
from obt.eda.xilinx import vivado

deco = deco.Deco()

epilog =  deco.orange("Example (vivado help): %s --batch -- -help\n"%sys.argv[0])
epilog += deco.orange("Example (vivado tcl REPL): %s --tcl"%sys.argv[0])
epilog += deco.orange("Example (user shell command): %s --exec -- lsb_release -a"%sys.argv[0])

parser = argparse.ArgumentParser(description='Launch command in EDA Docker Containers',
                                 epilog=epilog)
parser.add_argument('--gui', action="store_true", help=deco.yellow('Launch Vivado GUI'))
parser.add_argument('--batch', action="store_true", help=deco.yellow('Launch Vivado in batch mode, seperate vivado arguments using -- arg break'))
parser.add_argument('--tcl', action="store_true", help=deco.yellow('Launch Vivado in tcl-shell mode'))
parser.add_argument('--shell', action="store_true", help=deco.yellow('Launch Vivado/LiteX enabled bash'))
parser.add_argument('--exec', action="store_true", help=deco.yellow('exec command in Vivado/Litex container'))
parser.add_argument('--posttag', help=deco.yellow('tag container with <name> post execution'))
parser.add_argument('remainderargs', nargs=argparse.REMAINDER)

_args = vars(parser.parse_args())

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

cwd = path.Path(os.getcwd())
vctx = vivado.Context(hostdir=cwd)
tag = None

if _args["posttag"]:
  tag = path.Path(_args["posttag"])

if _args["gui"]:
  vctx.env["_JAVA_OPTIONS"] = "-Dawt.useSystemAAFontSettings=on "\
                              "-Dswing.aatext=true "\
                              "-Dswing.defaultlaf=com.sun.java.swing.plaf.gtk.GTKLookAndFeel "\
                              "-Dswing.crossplatformlaf=com.sun.java.swing.plaf.gtk.GTKLookAndFeel"
  vctx.run(args=[],posttag=tag)
elif _args["tcl"]:
  vctx.run(interactive=True,args=["-mode","tcl","-nojournal","-nolog"],posttag=tag)
elif _args["batch"]:
  remargs = _args["remainderargs"][1:]
  vctx.run_batch(args=remargs,posttag=tag)
elif _args["shell"]:
  vctx.shell()
elif _args["exec"]:
  remargs = _args["remainderargs"][1:]
  vctx.shell_command(remargs,posttag=tag)
else:
  assert(False)
