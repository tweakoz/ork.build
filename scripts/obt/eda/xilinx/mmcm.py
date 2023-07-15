#!/usr/bin/env python3

import os, fileinput
from obt import path, pathtools
from obt.eda.xilinx import vivado

########################################################

class OutClock:
  def __init__(self,freq,phaseoffset):
    self._frequency = freq          # Mhz
    self._phaseoffset = phaseoffset # Degrees

########################################################
def generate(vivctx,
             INSTANCENAME="systemclocks",
             differential=True,
             INP_FREQ=100.0,# mhz
             INP_NAME="SYSCLK_P",
             outclocks=[]):
  #############################
  # clear out IP_DIR
  #############################
  IP_DIR = vivctx.hostdir/".gen"/INSTANCENAME
  os.system("rm -rf %s"%IP_DIR)
  #############################
  num_outputs = len(outclocks)
  assert(num_outputs>=1)
  assert(num_outputs<=4)
  INP_PERIOD_NANOS = round(1000.0 / INP_FREQ,3);
  MMCMDICT = {
    "CONFIG.NUM_OUT_CLKS": num_outputs,
    "CONFIG.USE_MIN_POWER": True,
    "CONFIG.PRIM_IN_FREQ": INP_FREQ,
    "CONFIG.USE_SAFE_CLOCK_STARTUP": True,
    "CONFIG.JITTER_SEL": "No_Jitter",
    "CONFIG.FEEDBACK_SOURCE": "FDBK_AUTO",
    "CONFIG.MMCM_CLKIN1_PERIOD": INP_PERIOD_NANOS,
  }
  #############################
  if differential:
    MMCMDICT["CONFIG.PRIM_SOURCE"]="Differential_clock_capable_pin"
  #############################
  index = 0
  for item in outclocks:
    out = outclocks[index]
    index += 1
    MMCMDICT["CONFIG.CLKOUT%d_REQUESTED_OUT_FREQ"%index]=out._frequency
    MMCMDICT["CONFIG.CLKOUT%d_REQUESTED_PHASE"%index]=out._phaseoffset
    MMCMDICT["CONFIG.CLKOUT%d_DRIVES"%index]="BUFGCE" # BUFG,BUFGCE
    MMCMDICT["CONFIG.CLKOUT%d_USED"%index] = True
  #############################
  vivctx.genIP(tclname="%s.tcl"%INSTANCENAME,
               IPID="clk_wiz",
               VERSION="6.0",
               INSTANCENAME=INSTANCENAME,
               IPPROPERTIES=MMCMDICT)
  #############################
  verilog_out = IP_DIR/("%s_clkwiz.v"%INSTANCENAME)
  xcd_out = IP_DIR/("%s.xdc"%INSTANCENAME)
  #############################
  # fixup Differential clock input since the clk_wiz is hosed
  #  (it disables PRIMARY_PORT in differential mode)
  # https://forums.xilinx.com/xlnx/board/crawl_message?board.id=DEENBD&message.id=13910
  ###########################################################
  with fileinput.FileInput(xcd_out, inplace=True) as file:
    for line in file:
        print(line.replace("clk_in1_p", INP_NAME), end='')
