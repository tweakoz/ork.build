#!/usr/bin/env python3

import os, fileinput
from obt import path, pathtools
from obt.eda.xilinx import vivado

########################################################
def generate(vivctx,
             INSTANCENAME="sdiio"):
  #############################
  # clear out IP_DIR
  #############################
  IP_DIR = vivctx.hostdir/".gen"/INSTANCENAME
  os.system("rm -rf %s"%IP_DIR)
  #############################
  SDIOUTDICT = {
    "CONFIG.INCLUDE_RX_EDH_PROCESSOR": False
  }
  #############################
  index = 0
  #############################
  vivctx.genIP(tclname="%s.tcl"%INSTANCENAME,
               IPID="v_smpte_sdi",
               VERSION="3.0",
               INSTANCENAME=INSTANCENAME,
               IPPROPERTIES=SDIOUTDICT)
  #############################
  verilog_out = IP_DIR/("%s_v_smpte_sdi.v"%INSTANCENAME)
  xcd_out = IP_DIR/("%s.xdc"%INSTANCENAME)

#create_ip -name v_smpte_sdi -vendor xilinx.com -library ip -version 3.0 -module_name v_smpte_sdi_0
