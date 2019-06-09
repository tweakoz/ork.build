#!/usr/bin/env python3

import os, sys, pathlib, argparse, shlex, subprocess, pprint
import ork.deco
import ork.path
import ork.git
from ork.command import Command
import json

###############################################
# create or load litex env cache
#  we cache these (via a json env dictionary)
#  because they are quite heavy
#  to create anew
###############################################

def import_env_from_bashsource(envdir,triple):
  bashfile = envdir/"scripts"/"enter-env.sh"
  cachfile = envdir/(".cache_load_env_%s.sh"%triple)
  if False:#cachfile.exists():
      with open(str(cachfile),"rt") as f:
        delta_dict = json.loads(f.read())
      for key in delta_dict:
          os.environ[key] = delta_dict[key]
          print("key<%s> val<%s>"%(deco.key(key),deco.val(delta_dict[key])))
      pass
  else:
      #############################################
      # just setting env vars does not seem to do the trick
      #  we need to set vars on the bash source commandline
      #############################################
      var_str =  "PLATFORM=%s "%triple["PLATFORM"]
      var_str += "CPU=%s "%triple["CPU"]
      var_str += "TARGET=%s "%triple["TARGET"]
      var_str += "FIRMWARE=%s "%triple["FIRMWARE"]
      #############################################
      command = shlex.split("env -i bash -c '%s source %s && env'"%(var_str,str(bashfile)))
      proc = subprocess.Popen(command, stdout = subprocess.PIPE)
      #############################################
      litex_keys = {
        "BIOS_FILE",
        "CLANG",
        "CPU",
        "CPU_VARIANT",
        "CPU_ARCH",
        "DEFAULT_TARGET",
        "FIRMWARE",
        "FIRMWARE_FILEBASE",
        "FULL_PLATFORM",
        "GATEWARE_FILEBASE",
        "HAVE_FPGA_TOOLCHAIN",
        "HAVE_XILINX_ISE",
        "HAVE_XILINX_TOOLCHAIN",
        "HAVE_XILINX_VIVADO",
        "HDMI2USB_ENV",
        "IMAGE_FILE",
        "LITEX_EXTRA_CMDLINE",
        "MAKE_LITEX_EXTRA_CMDLINE",
        "MISOC_EXTRA_CMDLINE",
        "OVERRIDE_FIRMWARE",
        "PLATFORM",
        "PATH",
        "PLATFORM_EXPANSION",
        "PROG",
        "PYTHONHASHSEED",
        "SHLVL",
        "TARGET_BUILD_DIR",
        "TFTP_SERVER_PORT",
        "TFTPD_DIR",
        "TFTP_IPRANGE",
        "TARGET",
        "TFTP_DIR",
      }
      for line in proc.stdout:
        decoded = line.decode('utf-8')
        decoded = decoded.replace("\n","")
        (key, _, value) = decoded.partition("=")
        print(key,value)
        if key in litex_keys:
            os.environ[key] = value
      proc.communicate()

      delta_dict = dict()

      for key in litex_keys:
        if key in os.environ:
          delta_dict[key] = os.environ[key]
          print("key<%s> val<%s>"%(deco.key(key),deco.val(delta_dict[key])))

      delta_dict["ZEPHYR_BASE"]=str(env_dir/"build"/"zephyr_sdk")

      with open(str(cachfile),"wt") as f:
        json.dump(delta_dict, f)
        f.close()

###############################################

deco = ork.deco.Deco()

parser = argparse.ArgumentParser(description='ork.build litex env launcher')
parser.add_argument('--cpu', metavar="cpu", help='cpu(lm32,or1k,riscv32)' )
parser.add_argument("--platform", metavar="platform", help="platform(cmod_a7,nexysvideo,arty)")
parser.add_argument('--target', metavar="target", help='target(base,net)' )
parser.add_argument('--firmware', metavar="firmware", help='target(zephyr)' )
parser.add_argument('--exec', metavar="exec", help='command to execute in-env' )
parser.add_argument('--init', action="store_true", help='command to execute in-env' )
parser.add_argument('--shell', action="store_true", help='enter shell in-env' )
parser.add_argument('--update', action="store_true", help='update litex env' )

args = vars(parser.parse_args())

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

#################################################

cpu = args["cpu"]
platform = args["platform"]
target = args["target"]
firmware = args["firmware"]
triple = "%s_%s_%s_%s" % (platform,cpu,target,firmware)

triple_dict = {
    "CPU": cpu,
    "TARGET": target,
    "PLATFORM": platform,
    "FIRMWARE": firmware,
}

#################################################

env_dir = ork.path.builds()/"litex_env"

os.environ["PLATFORM"]=platform
os.environ["CPU"]=cpu
os.environ["TARGET"]=target
os.environ["FIRMWARE"]=firmware
os.environ["LITEX_TRIPLE"]=triple
os.environ["ORK_PROJECT_NAME"]=("obt-lx/%s"%triple)
os.environ["LITEX_TRIPLE"]=triple
os.environ["ZEPHYR_SDK_VERSION"] = "0.10.1-rc1"
os.environ["ZEPHYR_SDK_INSTALL_DIR"]=str(env_dir/"build"/"zephyr_sdk")
os.environ["ZEPHYR_TOOLCHAIN_VARIANT"]="zephyr"
os.environ["BOARD"]="litex_vexriscv"
#pip3 install -r scripts/requirements.txt

os.environ["LITEX_BIN_DIR"] = str(env_dir/"build"/"conda"/"bin")

curdir = os.getcwd()

#################################################

print( "cpu<%s>" % deco.key(cpu) )
print( "platform<%s>" % deco.key(platform) )
print( "target<%s>" % deco.key(target) )
print( "triple<%s>" % deco.key(triple) )
print( "env_dir<%s>" % deco.key(env_dir) )

###############################################
# create litex-env if it does not already exist
#################################################
if False == env_dir.exists() or (args["init"]==True):
    if env_dir.exists():
        print("obliterating old litex install at<%s>" % str(deco.path(env_dir)))
        os.system("rm -rf %s"%str(env_dir))
    ork.git.Clone("https://github.com/timvideos/litex-buildenv", \
                  env_dir, \
                  "master", \
                  True )
    os.system(str(env_dir/"scripts"/"bootstrap.sh"))
    os.system(str(env_dir/"scripts"/"download-env.sh"))
    os.system(str(env_dir/"scripts"/"build-zephyr.sh"))
###############################################
# import env from bash source
###############################################
import_env_from_bashsource(env_dir,triple_dict)
#################################################
# enter or launch in litex-env
###############################################
cmdlist = [ \
    ("%s/bin/init_env.py"%str(ork.path.root())),
    "--quiet",
    "--stack", str(ork.path.prefix())
]
###############################################
# create litex-env if it does not already exist
#################################################
if args["update"]==True:
    os.system(str(env_dir/"scripts"/"download-env.sh"))
if args["shell"]==True:
    Command(cmdlist).exec()
#################################################
elif args["exec"]!=None:
    cmdlist += ["--command"]
    print(args["exec"])
    cmdlist += [args["exec"]]
    Command(cmdlist).exec()
###############################################
