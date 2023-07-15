#!/usr/bin/env python3
###########################################################
# lsusbx : fancy usb device lister
#  @ 2019 Michael T. Mayers : michael@tweakoz.com
#  license: go to town...
# todo: make it faster and prettier
###########################################################
import subprocess, sys, os, re
from pathlib import Path
import pyudev
import obt.deco
deco = obt.deco.Deco()

class devinfo:
    def __init__(self,name,usbpos):
        self._name = name
        self._usbpos = usbpos
        self._devtype = ""
        self._model = ""
        self._modelenc = ""
        self._vendor = ""
        self._vendordb = ""
        self._ttyname = ""
        self._drivers = set()
        self._serial = ""
        self._speed = 0
    def vendorShort(self):
        lv = len(self._vendor)
        lvdb = len(self._vendordb)
        vendor = self._vendor
        if (lvdb>0) and (lvdb<lv) and (lv>8):
            vendor = self._vendordb
        return vendor
    def modelShort(self):
        return self._modelenc

devices = dict()

udev = pyudev.Context()

############################################################
# gather devices
############################################################

all_devices = udev.list_devices(subsystem="usb")

for d in all_devices:
   #print(dict(d))
   DEVTYPE = d.get("DEVTYPE")
   if DEVTYPE=="usb_device": # leaf devices
     busnum = d.attributes.get("busnum")
     devnum = d.attributes.get("devnum")
     devpath = d.attributes.get("devpath")
     speed = d.attributes.get("speed")
     pos = "%03d:%03d"%(int(busnum),int(devnum))
     #print(d.sys_name,busnum,devnum,devpath )
     devi = devinfo(pos,pos)
     MODELENC = d.get("ID_MODEL_ENC")
     VENDOR = d.get("ID_VENDOR_ENC")
     VENDORDB = d.get("ID_VENDOR_FROM_DATABASE")
     SERIAL = d.get("ID_SERIAL_SHORT")
     if VENDOR!=None:
       devi._vendor=bytes(VENDOR, "utf-8").decode("unicode_escape")
     if VENDORDB!=None:
       devi._vendordb=bytes(VENDORDB, "utf-8").decode("unicode_escape")
     if MODELENC!=None:
       devi._modelenc=bytes(MODELENC, "utf-8").decode("unicode_escape")
     if SERIAL!=None:
       devi._serial=bytes(SERIAL, "utf-8").decode("unicode_escape")
     devi.speed = speed
     devices[pos]=devi

############################################################
# gather interfaces
############################################################

for d in all_devices:
   DEVTYPE = d.get("DEVTYPE")
   if DEVTYPE=="usb_interface": # endpoints in device
     p = d.parent
     #print(dict(p))
     busnum = p.attributes.get("busnum")
     devnum = p.attributes.get("devnum")
     devpath = p.attributes.get("devpath")
     if busnum!=None and devnum!=None:
      pos = "%03d:%03d"%(int(busnum),int(devnum))
      assert(pos in devices)
      devi = devices[pos]
      DRIVER = d.get("DRIVER")
      MODEL = d.get("ID_MODEL_FROM_DATABASE")
      if DRIVER!=None:
         devi._drivers.add(DRIVER)
      if MODEL!=None:
         devi._model=MODEL

############################################################
# gather tty's
############################################################

for device in udev.list_devices(subsystem="tty",ID_BUS="usb"):
    #print(device)
    p = device.find_parent(subsystem="usb")
    if p!=None:
        k = device.sys_name
        pp = p.parent
        busnum = pp.attributes.get("busnum")
        devnum = pp.attributes.get("devnum")
        pos = "%03d:%03d"%(int(busnum),int(devnum))
        assert(pos in devices)
        devi = devices[pos]
        devi._ttyname = device.sys_name

############################################################

devnull = open(os.devnull, 'w')

def getlines(cmd):
    lines = subprocess.check_output(cmd,
                                    shell=True,
                                    stderr=devnull,
                                    universal_newlines=True).split("\n")
    return lines

usbitems = getlines("lsusb")

###############################
def rgb256(r,g,b):
    return deco.rgb256(r,g,b)
###############################
def reset():
    return deco.reset()
###############################
def rgbstr(r,g,b,string):
    return deco.rgbstr(r*255,g*255,b*255, str(string) )
###############################

byloc = dict()
for item in usbitems:
    columns = item.split(" ")
    if len(columns)>5:
     bus = columns[1]
     dev = columns[3][0:3]
     ifclass = ""

     ##############################
     # this is the code that is taking too long, optimize it before turning it back on..
     ##############################
     #verbose = getlines("lsusb -s %s:%s -v"%(bus,dev))
     #for l in verbose:
     #    if l.find("bInterfaceClass")>=0:
     #        col = l.split()
     #        ifclass = " ".join(col[2:])
     ##############################

     pos = "%s:%s" % (bus,dev)
     out = "[%s] "%rgbstr(1,1,0,pos)

     assert (pos in devices)

     device = devices[pos]
     if device._model!="":
       ifclass = device._model

     if ifclass!="":
        if "hub" in device._drivers:
            out += "%s  " % rgbstr(.5,.8,.1,ifclass)
        elif "usbhid" in device._drivers:
            out += "%s  " % rgbstr(.5,.5,1,ifclass)
        elif "uvcvideo" in device._drivers or "ov534" in device._drivers:
            out += "%s  " % rgbstr(1,.3,.9,ifclass)
        elif "snd-usb-audio" in device._drivers:
            out += "%s  " % rgbstr(0.8,.2,1,ifclass)
        elif "usb-storage" in device._drivers:
            out += "%s  " % rgbstr(.7,1,1,ifclass)
        elif device._ttyname!="":
            out += "%s  " % rgbstr(1,.5,0,ifclass)
        else:
            out += "%s  " % rgbstr(.7,.8,.7,ifclass)

     out += "spd<%s> "%device.speed.decode('utf-8')

     if len(device._drivers)>0:
      out += "drv<"
      index = 0
      count = len(device._drivers)
      for drv in device._drivers:
        out += "%s" % rgbstr(1,1,1,drv)
        if count>1 and index<(count-1):
          out += " "
        index += 1

      out += "> "

     out += "product<%s " % rgbstr(.9,.6,.7,device.vendorShort())
     out += "%s> " % rgbstr(.7,.7,.8,device.modelShort())

     if device._ttyname!="":
        out += "tty<%s> " % rgbstr(1,.7,.3,device._ttyname)
     if device._serial!="":
        out += "sn<%s> " % rgbstr(1,1,.5,device._serial)

     byloc["%s:%s"%(bus,dev)]=out
     print(".",end="",flush=True)

print("")
sitems = sorted(byloc.keys(),reverse=False)
prv_bus = ""
for item in sitems:
    bus = item[0:3]
    if bus!=prv_bus:
       prv_bus = bus
       print()
    print(byloc[item])
