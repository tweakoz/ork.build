#!/usr/bin/env python3

from obt import path, pathtools, utils, deco
import os, argparse, sys
deco = deco.Deco()

sbase = path.zephyr_base()/"samples"

samples = {
    "helloworld": sbase/"hello_world",
    "synchro": sbase/"synchronization",
    "cppsynchro": sbase/"cpp_synchronization",
    "ethernet": sbase/"net"/"eth_native_posix",
    "getline": sbase/"subsys"/"console"/"getline",
    #"blinky": sbase/"basic"/"blink_led",
    #"rgbled": sbase/"basic"/"rgb_led",
    #"gpio": sbase/"drivers"/"gpio"
    #"servo": sbase/"basic"/"servo_motor",
    #"threads": sbase/"basic"/"threads",
}

parser = argparse.ArgumentParser(description='zephry sample builder')
parser.add_argument('--list', action="store_true" )
parser.add_argument("--build", metavar="samplename")


args = vars(parser.parse_args())

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)


if args["list"]==True:
    for key in samples:
        val = samples[key]
        print("%s: %s"%(deco.key(key),deco.path((val))))
elif args["build"]!=None:
    key = args["build"]
    if key in samples:
      build_dir = path.builds()/("litexzephyrsample-%s"%key)
      src_dir = samples[key]
      pathtools.mkdir(build_dir,clean=True)
      pathtools.chdir(build_dir)
      os.system("cmake -DBOARD=litex_vexriscv %s"%str(src_dir))
      os.system("make -j %d"%utils.num_cores)
    else:
      print("unknown sample<%s>"%key)
