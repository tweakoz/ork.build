######################################################################
# Vivado/PetaLinuX/Litex/EDA container operations
######################################################################

import os
import obt.path
import obt.command
import obt.deco
import obt.pathtools

import os, platform
from string import Template

######################################################################

#builddir = obt.path.builds()/"petalinux-docker"
deco = obt.deco.Deco()

#if not builddir.exists() :
 # print(deco.yellow("You must install the eda containers first!"))
  #assert(False)

######################################################################

DISPLAY=os.environ["DISPLAY"]
HOME=obt.path.Path(os.environ["HOME"])

osname = platform.system()

######################################################################

if osname=="Darwin":
 os.system("xhost + 127.0.0.1")
 DISPLAY="host.docker.internal:0"

xauth_host = str(HOME/".Xauthority")
xauth_cont = "/home/vivado/.Xauthority"
proj_host = str(HOME/"Xilinx")
proj_cont = "/home/eda/project"

######################################################################
# IP generation template tcl script
######################################################################

TCL_GENIP_TEMPLATE = Template("""
create_project -part $PARTNAME -in_memory -verbose

set outputDir $IPDIR

create_ip -name $IPID -vendor $VENDOR -library $LIBRARY -version $VERSION -module_name $INSTANCENAME -dir $$outputDir

set_property -dict [list $IPPROPERTIES] [get_ips $INSTANCENAME]

generate_target {instantiation_template} [get_files $INSTANCENAME.xci]

generate_target all [get_files  $INSTANCENAME.xci]

catch { config_ip_cache -export [get_ips -all $INSTANCENAME] }

export_ip_user_files -of_objects [get_files $INSTANCENAME.xci] -no_script -sync -force -quiet
""")

######################################################################

class Context:
  #########################
  def __init__(self,
               hostdir=None,
               containerdir="/tmp/build",
               FPGAPART=None,
               postremove=True):
    #####################
    assert(hostdir!=None)
    #####################
    self.fpgapart = FPGAPART
    self.hostdir = obt.path.Path(hostdir)           # directory to map to containerdir
    self.containerdir = obt.path.Path(containerdir)
    self.postremove = postremove
    self.posttag = None
    self.dirmaps={
      hostdir: containerdir
    }
    self.env={}
  #########################
  def _core_commandline(self,dockerargs=[]):
    cline =  ["docker","run","-it"]
    cline += ["-e","DISPLAY=%s"%DISPLAY]
    cline += ["--net=host","--ipc=host"]
    cline += ["-v","/tmp/.X11-unix:/tmp/.X11-unix"]
    cline += ["-v","%s:%s"%(xauth_host,xauth_cont)]
    cline += ["-v","%s:%s"%(proj_host,proj_cont)]
    for K in self.dirmaps.keys():
      V = self.dirmaps[K]
      cline += ["-v","%s:%s"%(str(K),str(V))]
    for K in self.env.keys():
      V = self.env[K]
      cline += ["--env","%s=%s"%(str(K),str(V))]
    cline += ["-w",str(self.containerdir)]
    if self.postremove:
      cline += ["--rm"]
    cline += dockerargs
    cline += ["eda:2020.1"]
    return cline
  #########################
  def _posttag_preamble(self,posttag=None):
    if posttag!=None:
      obt.command.system(["rm","-f","container.cid"])
      return ["--cidfile=./container.cid"]
    else:
      return []
  #########################
  def _posttag_postamble(self,posttag=None):
    if posttag!=None:
      with open('container.cid', 'r') as file:
        cid = file.read()
        assert(type(posttag)==str)
        obt.command.system(["docker",
                            "commit",cid,
                            posttag])
  #########################
  def run(self,
          interactive=False,
          posttag=None,
          args=[]):
    obt.pathtools.chdir(self.hostdir)
    preargs = self._posttag_preamble(posttag=posttag)
    cline =  self._core_commandline(dockerargs=preargs)
    #if self.postremove:
    #  cline += ["--rm"]
    cline += ["/opt/xilinx/Vivado/2020.1/bin/vivado"]+args
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
    rval = None
    if interactive:
      rval = obt.command.system(cline)
    else:
      rval = obt.command.run_filtered(cline,on_line=filter_line)
    self._posttag_postamble(posttag=posttag)
    return rval
  ######################################################################
  def run_batch(self,args,posttag=None):
    return self.run(posttag=posttag,
                    args=["-mode",
                          "batch",
                          "-nojournal",
                          "-nolog"]+args)
  ######################################################################
  def run_tclscript(self,tclscriptname,posttag=None):
    return self.run_batch(args=["-source",tclscriptname])
  ######################################################################
  def shell(self):
    obt.pathtools.chdir(self.hostdir)
    cline =  self._core_commandline()
    cline += ["/bin/bash"]
    return obt.command.system(cline)
  ######################################################################
  def shell_command(self,args,posttag=None,working_dir=None):
    if working_dir==None:
      working_dir=self.hostdir
    obt.pathtools.chdir(working_dir)
    preargs = self._posttag_preamble(posttag=posttag)
    cline =  self._core_commandline(dockerargs=preargs)
    cline += ["/bin/bash","-l","-c"]
    cline += ['"'+" ".join(args)+'"']
    rval = obt.command.system(cline)
    self._posttag_postamble(posttag=posttag)
    return rval
  ######################################################################
  # generate vivado IP with parameters
  ######################################################################

  def genIP(self,
            tclname=None,
            VENDOR="xilinx.com", # vivado built in IP
            LIBRARY="ip",        # vivado built in IP
            IPID=None,
            VERSION=None,
            INSTANCENAME=None,
            IPPROPERTIES=None):

    assert(self.fpgapart!=None)
    assert(tclname!=None)
    assert(IPID!=None)
    assert(tclname!=None)
    assert(tclname!=None)
    assert(tclname!=None)

    os.system("mkdir -p %s"%(self.hostdir/".gen"))


    tclhostfilename = self.hostdir/".gen"/tclname
    tclcontfilename = self.containerdir/".gen"/tclname

    IPPROPERTIESSTR = ''.join(['%s {%s} ' % (key, str(value)) for (key, value) in IPPROPERTIES.items()])
    IPPROPERTIESSTR = IPPROPERTIESSTR.replace("True","true")
    IPPROPERTIESSTR = IPPROPERTIESSTR.replace("False","false")
    print(IPPROPERTIESSTR)


    tclstr = TCL_GENIP_TEMPLATE.substitute(IPDIR=self.containerdir/".gen",
                                           IPID=IPID,
                                           VENDOR=VENDOR,
                                           VERSION=VERSION,
                                           LIBRARY=LIBRARY,
                                           PARTNAME=self.fpgapart,
                                           INSTANCENAME=INSTANCENAME,
                                           IPPROPERTIES=IPPROPERTIESSTR)

    with open(tclhostfilename,"wt") as f:
      f.write(tclstr)

    rval = self.run_tclscript(tclcontfilename)

    os.system("rm -rf %s"%(self.hostdir/".ip_user_files"))
    return rval
