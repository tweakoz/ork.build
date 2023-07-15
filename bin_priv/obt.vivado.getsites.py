#!/usr/bin/env python3
###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import argparse, sys, os, tempfile
from string import Template
from obt import deco, path
from obt.eda.xilinx import vivado

deco = deco.Deco()

###############################################################################

epilog = deco.orange("Example (vivado help): %s --batch -- -help"%sys.argv[0])
parser = argparse.ArgumentParser(description='Launch command in EDA Docker Containers',
                                 epilog=epilog)
parser.add_argument('--prim', help=deco.yellow('primitive type'))
parser.add_argument('--partid', help=deco.yellow('fpga partid'))

_args = vars(parser.parse_args())

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

###############################################################################

partid = _args["partid"]
assert(partid!=None)

###############################################################################
#set site [get_sites GTHE4_CHANNEL_X0Y19]
#report_property -all [get_package_pins A8]
#report_property -all $site
#get_property CLOCK_REGION $site
#get_property PIN_FUNC [get_package_pins A7] #MGTHTXN3_227
#get_site_pins -of $site
#get_bels -of $site # GTHE4_CHANNEL_X0Y22/GTHE4_CHANNEL GTHE4_CHANNEL_X0Y22/IPAD1
#                     GTHE4_CHANNEL_X0Y22/IPAD2 GTHE4_CHANNEL_X0Y22/OPAD1 GTHE4_CHANNEL_X0Y22/OPAD2

#get_sites [get_package_pins -filter { PIN_FUNC =~ *MGTHTXP3_227* }] # GTHE4_CHANNEL_X0Y19

#get_bel_pins -of $site
#get_tiles -of_objects $site # GTH_QUAD_RIGHT_X69Y300

topstr = "module top(); endmodule"

TEMPLATE = Template("""
puts "Getting Sites"
create_project -part $PARTNAME -in_memory -verbose
read_verilog [glob /tmp/build/*.v]
synth_design -rtl -top top
set items [ get_sites -regexp "GTHE4_.*"]
#set items [ get_sites]
foreach item $$items {
  puts "site<$$item>"
  set site [get_sites $$item]
  set pins [ get_site_pins ‐of $$site ]
  puts "site<$$item> pins<$$pins>"
}
""")
tclstr = TEMPLATE.substitute(PARTNAME=partid)

###############################################################################

with tempfile.TemporaryDirectory() as tempdir:
  tempdirname = path.Path(tempdir)
  vctx = vivado.Context(hostdir=tempdirname,FPGAPART=partid)
  tclhostfilename = vctx.hostdir/"getsites.tcl"
  tclcontfilename = vctx.containerdir/"getsites.tcl"
  verhostfilename = vctx.hostdir/"top.v"
  vercontfilename = vctx.containerdir/"top.v"
  with open(tclhostfilename,"wt") as f:
    f.write(tclstr)
  with open(verhostfilename,"wt") as f:
    f.write(topstr)
  rval = vctx.run_tclscript(tclcontfilename)
