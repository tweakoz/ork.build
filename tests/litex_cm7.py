#!/usr/bin/env python3

import argparse, os, sys, time
from obt import path, pathtools, command, env, log

litex_dir = path.builds()/"litex"
litex_boards_dir = litex_dir/"litex-boards"
litex_targets_dir = litex_boards_dir/"litex_boards"/"targets"

soc_dir = path.builds()/"litex1_cm7"

parser = argparse.ArgumentParser(description="")
parser.add_argument("-l", "--load", action="store_true")
parser.add_argument("-t", '--tty', metavar="tty", default="/dev/ttyUSB0", help='fpga programming tty' )
options = vars(parser.parse_args())

do_load = options["load"]

if "DEVTTY" in os.environ:
    tty = os.environ["DEVTTY"]
else:
    tty = options["tty"]

print(tty)

if do_load:
    loader = soc_dir/"software"/"bios"/"bios.bin"
    command.run([
      "djtgcfg",
      "prog",
      "-d", "CmodA7",
      "-i", "0",
      "-f", soc_dir/"gateware"/"digilent_cmod_a7.bit" ], do_log=True)
    print( "waiting a bit...")
    time.sleep(3)
    command.run([ "litex_term",
      "--speed", "115200",
      "--serial-boot",
      #"--kernel",loader,
      tty], do_log=True)
    #  "--kernel-adr","cff00000"])
else:
    cmd = [
        litex_targets_dir/"digilent_cmod_a7.py",
        "--output-dir", soc_dir,
        "--build",
        "--cpu-type", "vexriscv",
        "--cpu-variant", "linux",
        #"--cpu-type", "vexriscv_smp",
        #"--cpu-variant", "linux",
        #"--cpu-count", "2",
        #"--with-fpu",
        #"--icache-size", "4096",
        #"--dcache-size", "4096",
        #"--with-wishbone-memory",
        #"--uart-name=crossover+uartbone",
        #"--csr-csv=csr.csv",
        "--sys-clk-freq", "120e6",
    ]
    command.run(cmd,do_log=True)


