#!/usr/bin/env python3

import os, fileinput
from ork import path, pathtools
from ork.eda.xilinx import vivado

########################################################
def generate(vivctx,
             INSTANCENAME="sdigt"):
  #############################
  # clear out IP_DIR
  #############################
  IP_DIR = vivctx.hostdir/".gen"/INSTANCENAME
  os.system("rm -rf %s"%IP_DIR)
  #############################
  SDIGTPROPS = {
    "CONFIG.C_GT_TYPE": "GTHE4",
    "CONFIG.C_LINE_RATE": "3G-SDI",
    "CONFIG.C_SDI_LINKS": 1,
    "CONFIG.C_DATA_FLOW": "Duplex",
    "CONFIG.C_GT_TX_DATAWIDTH_INTF_0": 20,
    "CONFIG.C_GT_RX_DATAWIDTH_INTF_0": 20,
    "CONFIG.SupportLevel": 1,
    "CONFIG.C_QPLL0_Refclk_Sel": "GTREFCLK0",
    "CONFIG.C_QPLL1_Refclk_Sel": "GTREFCLK1",
    #"CONFIG.C_CPLL_Refclk_Sel": "GTREFCLK0",
    "CONFIG.C_DRP_CLK_FREQ": 100.0,
    "CONFIG.C_EN_PICXO_PORTS": False,
    "CONFIG.C_SDI_MODE": "PICXO",
    "CONFIG.C_Tx_PLL_Selection_INTF_0": "QPLL0",
    "CONFIG.C_Rx_PLL_Selection_INTF_0": "QPLL0",
    "CONFIG.C_Tx_PLL2_Selection_INTF_0": "QPLL1",
    "CONFIG.C_Rx_PLL2_Selection_INTF_0": "QPLL1",
  }
  #############################
  index = 0
  #############################
  return vivctx.genIP(tclname="%s.tcl"%INSTANCENAME,
                      IPID="uhdsdi_gt",
                      VERSION="2.0",
                      INSTANCENAME=INSTANCENAME,
                      IPPROPERTIES=SDIGTPROPS)
  #############################
