#!/usr/bin/env python3

import os, sys, pathlib, argparse, shlex, subprocess, pprint
import ork.deco
import ork.path
import ork.git
from ork.command import Command
import json

###############################################
# create or load litex env cache
###############################################

def import_env_from_bashsource(envdir,triple):
  bashfile = envdir/"scripts"/"enter-env.sh"
  cachfile = envdir/(".cache_load_env_%s.sh"%triple)
  print(cachfile)
  if cachfile.exists():
      with open(str(cachfile),"rt") as f:
        delta_dict = json.loads(f.read())
      print(delta_dict)
      for key in delta_dict:
          os.environ[key] = delta_dict[key]
          print("key<%s> val<%s>"%(deco.key(key),deco.val(delta_dict[key])))
      pass
  else:
      command = shlex.split("env -i bash -c 'source %s && env'"%str(bashfile))
      proc = subprocess.Popen(command, stdout = subprocess.PIPE)

      litex_keys = {
        "MISOC_EXTRA_CMDLINE",
        "PATH",
        "BIOS_FILE",
        "PROG",
        "CPU_VARIANT",
        "FIRMWARE",
        "HAVE_FPGA_TOOLCHAIN",
        "PYTHONHASHSEED",
        "IMAGE_FILE",
        "HAVE_XILINX_ISE",
        "LITEX_EXTRA_CMDLINE",
        "HAVE_XILINX_TOOLCHAIN",
        "TARGET_BUILD_DIR",
        "HDMI2USB_ENV",
        "FULL_PLATFORM",
        "MAKE_LITEX_EXTRA_CMDLINE",
        "PLATFORM_EXPANSION",
        "TFTP_SERVER_PORT",
        "TFTPD_DIR",
        "HAVE_XILINX_VIVADO",
        "CPU_ARCH",
        "DEFAULT_TARGET",
        "PLATFORM",
        "CLANG",
        "TFTP_IPRANGE",
        "FIRMWARE_FILEBASE",
        "OVERRIDE_FIRMWARE",
        "SHLVL",
        "TARGET",
        "TFTP_DIR",
        "GATEWARE_FILEBASE",
        "CPU",
      }
      for line in proc.stdout:
        decoded = line.decode('utf-8')
        decoded = decoded.replace("\n","")
        print(decoded)
        (key, _, value) = decoded.partition("=")
        if key in litex_keys:
            os.environ[key] = value
      proc.communicate()

      delta_dict = dict()

      for key in litex_keys:
        delta_dict[key] = os.environ[key]
        print("key<%s> val<%s>"%(deco.key(key),deco.val(delta_dict[key])))

      with open(str(cachfile),"wt") as f:
        json.dump(delta_dict, f)
        f.close()
        assert(False)

###############################################

deco = ork.deco.Deco()

parser = argparse.ArgumentParser(description='ork.build litex env launcher')
parser.add_argument('--cpu', metavar="cpu", help='cpu(lm32,or1k,riscv32)' )
parser.add_argument("--platform", metavar="platform", help="platform(cmod_a7,nexysvideo)")
parser.add_argument('--target', metavar="target", help='target(base,net)' )
parser.add_argument('--exec', metavar="exec", help='command to execute in-env' )

args = vars(parser.parse_args())

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

#################################################

cpu = args["cpu"]
platform = args["platform"]
target = args["target"]
triple = "%s_%s_%s" % (platform,cpu,target)

#################################################

os.environ["PLATFORM"]=platform
os.environ["CPU"]=cpu
os.environ["TARGET"]=target
os.environ["LITEX_TRIPLE"]=triple
os.environ["ORK_PROJECT_NAME"]=triple

#################################################

print( "cpu<%s>" % deco.key(cpu) )
print( "platform<%s>" % deco.key(platform) )
print( "target<%s>" % deco.key(target) )
print( "triple<%s>" % deco.key(triple) )

#################################################

env_dir = ork.path.builds()/"litex_env"
print( "env_dir<%s>" % deco.key(env_dir) )

curdir = os.getcwd()
###############################################
# create litex-env if it does not already exist
#################################################
if False == env_dir.exists():
    print("does not exist")
    ork.git.Clone("https://github.com/timvideos/litex-buildenv", \
                  env_dir, \
                  "master", \
                  True )
    os.system(str(env_dir/"scripts"/"download-env.sh"))
###############################################
# import env from bash source
###############################################
import_env_from_bashsource(env_dir,triple)
#################################################
# enter or launch in litex-env
###############################################
cmdlist = [ \
    ("%s/bin/init_env.py"%str(ork.path.root())),
    "--quiet",
    "--stack", str(ork.path.prefix())
]
if args["exec"]!=None:
    cmdlist += ["--command"]
    print(args["exec"])
    cmdlist += [args["exec"]]

Command(cmdlist).exec()
###############################################
