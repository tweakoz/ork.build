import os
import ork.path
import ork.command
import ork.deco

import os, platform
from string import Template

######################################################################

builddir = ork.path.builds()/"petalinux-docker"
deco = ork.deco.Deco()

if not builddir.exists() :
  print(deco.yellow("You must install the eda containers first!"))
  assert(False)

######################################################################

DISPLAY=os.environ["DISPLAY"]
HOME=ork.path.Path(os.environ["HOME"])

osname = platform.system()

######################################################################

if osname=="Darwin":
 os.system("xhost + 127.0.0.1")
 DISPLAY="host.docker.internal:0"

xauth_host = str(HOME/".Xauthority")
xauth_cont = "/home/vivado/.Xauthority"
proj_host = str(HOME/"Xilinx")
proj_cont = "/home/vivado/project"

######################################################################

def run(dirmaps={},workingdir=None,args=[]):
  cline =  ["docker","run","-it","--rm"]
  cline += ["-e","DISPLAY=%s"%DISPLAY]
  cline += ["--net=host","--ipc=host"]
  cline += ["-v","/tmp/.X11-unix:/tmp/.X11-unix"]
  cline += ["-v","%s:%s"%(xauth_host,xauth_cont)]
  cline += ["-v","%s:%s"%(proj_host,proj_cont)]

  for K in dirmaps.keys():
    V = dirmaps[K]
    cline += ["-v","%s:%s"%(str(K),str(V))]

  if workingdir!=None:
    cline += ["-w",str(workingdir)]

  cline += ["petalinux:2020.1"]
  cline += ["/opt/Xilinx/Vivado/2020.1/bin/vivado"]+args
  #cline += ["find","."]
  def filter_line(inp):
    if inp.find("CRITICAL WARNING:")==0:
      print(deco.red(inp), end='')
    elif inp.find("ERROR:")==0:
      print(deco.red(inp), end='')
    elif inp.find("WARNING:")==0:
      print(deco.orange(inp), end='')
    elif inp.find("Resolution:")==0:
      print(deco.yellow(inp), end='')
    elif inp.find("Command:")==0:
      print(deco.rgbstr(255,128,255,inp), end='')
    elif inp.find("INFO")==0:
      print(deco.inf(inp), end='')
    elif inp.find("---------------------------------------------------------------------------------")==0:
      print(deco.rgbstr(128,128,128,inp), end='')
    elif inp.find("#")==0:
      print(deco.cyan(inp), end='')
    elif inp.find("Time (s): cpu")>=0:
      print(deco.rgbstr(128,128,128,inp), end='')
    else:
      print(deco.white(inp), end='')
  ork.command.run_filtered(cline,on_line=filter_line)

######################################################################
# IP generation template tcl script
######################################################################

TCL_GENIP_TEMPLATE = Template("""
create_project -part $PARTNAME -in_memory -verbose

set outputDir ./.gen
file mkdir $$outputDir

create_ip -name $IPID -vendor $VENDOR -library $LIBRARY -version $VERSION -module_name $INSTANCENAME -dir $$outputDir

set_property -dict [list $IPPROPERTIES] [get_ips $INSTANCENAME]

generate_target {instantiation_template} [get_files .gen/$INSTANCENAME/$INSTANCENAME.xci]

generate_target all [get_files  .gen/$INSTANCENAME/$INSTANCENAME.xci]

catch { config_ip_cache -export [get_ips -all $INSTANCENAME] }

export_ip_user_files -of_objects [get_files .gen/$INSTANCENAME/$INSTANCENAME.xci] -no_script -sync -force -quiet
""")

######################################################################
# generate vivado IP with parameters
######################################################################

def genIP(dirmaps=None,
          vivworkingdir=None,
          tclhostfilename=None,
          tclcontfilename=None,
          IPID=None,
          VENDOR=None,
          VERSION=None,
          LIBRARY=None,
          PARTNAME=None,
          INSTANCENAME=None,
          IPPROPERTIES=None):

  IPPROPERTIESSTR = ''.join(['%s {%s} ' % (key, str(value)) for (key, value) in IPPROPERTIES.items()])
  IPPROPERTIESSTR = IPPROPERTIESSTR.replace("True","true")
  IPPROPERTIESSTR = IPPROPERTIESSTR.replace("False","false")
  print(IPPROPERTIESSTR)


  tclstr = TCL_GENIP_TEMPLATE.substitute(IPID=IPID,
                                         VENDOR=VENDOR,
                                         VERSION=VERSION,
                                         LIBRARY=LIBRARY,
                                         PARTNAME=PARTNAME,
                                         INSTANCENAME=INSTANCENAME,
                                         IPPROPERTIES=IPPROPERTIESSTR)

  with open(tclhostfilename,"wt") as f:
    f.write(tclstr)

  run(dirmaps=dirmaps,
      workingdir=vivworkingdir,
      args=["-mode",
       "batch",
       "-nojournal",
       "-nolog",
       "-source",
       tclcontfilename])
