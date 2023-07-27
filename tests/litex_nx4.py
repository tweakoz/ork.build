#!/usr/bin/env python3

import argparse, os, sys
from obt import path, pathtools, command, env, log

litex_dir = path.builds()/"litex"
litex_boards_dir = litex_dir/"litex-boards"
litex_targets_dir = litex_boards_dir/"litex_boards"/"targets"

soc_dir = path.builds()/"litex1_nx4"

parser = argparse.ArgumentParser(description="")
parser.add_argument("-l", "--load", action="store_true")
parser.add_argument('--tty', metavar="tty", default=None, help='fpga programming tty' )
options = vars(parser.parse_args())

do_load = options["load"]

tty = "/dev/ttyUSB0"

if "DEVTTY" in os.environ:
    tty = os.environ["DEVTTY"]

if options["tty"] != None:
    tty = options["tty"]

print(tty)

if do_load:
    loader = soc_dir/"software"/"bios"/"bios.bin"
    command.run([
      "djtgcfg",
      "prog",
      "-d", "Nexys4",
      "-i", "0",
      "-f", soc_dir/"gateware"/"digilent_nexys4.bit" ])
    command.run([ "litex_term",
      "--speed", "115200",
      tty])
      #"--kernel",loader])
      #"--kernel-adr","cff00000"])
else:
    cmd = [
        litex_targets_dir/"digilent_nexys4.py",
        "--output-dir", soc_dir,
        "--build",
        "--sys-clk-freq", "125e6",
        #"--cpu-type", "vexriscv_smp",
        "--cpu-variant", "linux",
        #"--with-coherent-dma",
        #"--cpu-count", "2",
        #"--with-fpu",
        #"--icache-size", "4096",
        #"--dcache-size", "4096",
        #"--with-wishbone-memory",
        #"--cpu-type", "vexriscv",
        #"--cpu-variant", "minimal",
        #"--sys-clk-freq", "75e6",
    ]
    command.run(cmd,do_log=True)
