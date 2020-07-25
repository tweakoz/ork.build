#!/usr/bin/env python3

import os, fileinput
from ork import path, pathtools
from ork.eda.xilinx import vivado

########################################################
def generate(vivctx,
             INSTANCENAME="sditx"):
  #############################
  # clear out IP_DIR
  #############################
  IP_DIR = vivctx.hostdir/".gen"/INSTANCENAME
  os.system("rm -rf %s"%IP_DIR)
  #############################
  SDITXPROPS = {
    "CONFIG.C_VIDEO_INTF": "Native_Video",
    "CONFIG.C_LINE_RATE": "3G_SDI",
    "CONFIG.C_INCLUDE_AXILITE": False,
    "CONFIG.C_INCLUDE_EDH": False,
    "CONFIG.C_TX_INSERT_C_STR_ST352": False,
  }
  #############################
  index = 0
  #############################
  vivctx.genIP(tclname="%s.tcl"%INSTANCENAME,
               IPID="v_smpte_uhdsdi_tx_ss",
               VERSION="2.0",
               INSTANCENAME=INSTANCENAME,
               IPPROPERTIES=SDITXPROPS)
  #############################
