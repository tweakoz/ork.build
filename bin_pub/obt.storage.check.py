#!/usr/bin/env python3
###############################################################################

import mdstat, json, sys
from types import SimpleNamespace
from obt import command, deco as DECO 
import zfslib as zfs

###############################################################################

deco = DECO.Deco()

def convert_to_namespace(d):
  return SimpleNamespace(**{k: convert_to_namespace(v) if isinstance(v, dict) else v for k, v in d.items()})

###############################################################################

WHI = (255,255,255)
YEL = (255,255,0)
RED = (255,0,0)
GRN = (0,255,0)
BLU = (0,0,255)
LBLU = (128,128,255)
CYN = (0,255,255)
MAG = (255,0,255)
ORA = (255,128,0)
PUR = (128,0,128)

DK_WHI = (192,192,192)
DK_YEL = (192,192,0)
DK_RED = (192,0,0)
DK_GRN = (0,192,0)
DK_BLU = (0,0,192)
DK_CYN = (0,192,192)
DK_MAG = (192,0,192)
DK_ORA = (192,64,0)
DK_PUR = (64,0,64)
DK_LBLU = (64,64,128)

###############################################################################

def colstr(index, c1, c2, out_str):
  c = c2 if (index&1) else c1
  return deco.rgbstr(c[0],c[1],c[2], out_str)

###############################################################################

def sepstr(name=""):
  if(name==""):
    sepstr = deco.rgbstr(255,192,128,  "#"*80)
  else:
    name_len = len(name)
    l1 = 77 - name_len
    sepstr = "# " + name + " " + (l1 * "#")
    sepstr = deco.rgbstr(255,192,128,  sepstr)
  print(sepstr)

###############################################################################

sepstr()

###############################################################################

def check_drives():
  index = 0
  drivelist = {}
  cap = command.capture(["lsblk","-o","NAME,TYPE,SIZE"])
  cap_lines = cap.split("\n")
  for line in cap_lines:
    split_line = line.split()
    if len(split_line) > 1:
      #print(split_line)
      if split_line[1] == "disk":
        name = split_line[0]
        size = split_line[2]
        drivelist[name] = size

  for disk in drivelist:
    size = drivelist[disk]
    if "sd" in disk or "nvme" in disk:
      cmd_line = ["sudo","smartctl","-H","/dev/"+disk]
      cap = command.capture(cmd_line)
      cap_lines = cap.split("\n")
      status = "???"
      for line in cap_lines:  
        #print(line)
        if "self-assessment test result: PASSED" in line:
          status = "PASSED"
        elif "SMART Health Status: OK" in line:
          status = "OK"
        elif "FAIL" in line:
          status = "FAIL"
      
      
      colors = [MAG,DK_MAG]
      if status == "PASSED" or status == "OK":
        colors = [GRN,DK_GRN]
      elif status == "FAIL":
        colors = [RED,DK_RED]
      
      out_str = "%s(%s)"%(disk,size)
      drivelist[disk]= colstr(0,colors[0],colors[1],f"{out_str:<24}")
      sys.stdout.write(drivelist[disk] + "   ")
      sys.stdout.flush()
      if index % 4 == 3:
        sys.stdout.write("\n")
        sys.stdout.flush()
      index += 1
  print()
  return drivelist
  
###############################################################################
sepstr( "Checking block device SMART drive status (requires sudo)" )
DRIVE_STATS = check_drives()
sepstr()
###############################################################################

def check_zfs():
  conn = zfs.Connection(host='localhost')
  poolset = conn.load_poolset()
  index = 0
  for pool in poolset:
    
    size_mb = int(pool.get_property("size"))>>20
    free_mb = int(pool.get_property("free"))>>20
    allo_mb = int(pool.get_property("allocated"))>>20
    
    out_line = colstr(index,WHI,DK_WHI,"ZFS.pool: ")+deco.yellow("%10s "%pool.name)

    health = pool.get_property("health")
    C1 = WHI
    C2 = DK_WHI
    if health == "ONLINE":
      C1 = GRN
      C2 = DK_GRN
    else:
      C1 = RED
      C2 = DK_RED
    out_line += colstr(index,WHI,DK_WHI,"health: ")+colstr(index,C1,C2,("%8s "%health))
    #out_line += colstr(index,WHI,DK_WHI,"mountpoint: ")+colstr(index,YEL,DK_YEL,"%10s "%pool.get_property("mountpoint"))
    #out_line += colstr(index,WHI,DK_WHI,"free(MB): ")+colstr(index,YEL,DK_YEL,"%9s "%free_mb)
    #out_line += colstr(index,WHI,DK_WHI,"used(MB): ")+colstr(index,YEL,DK_YEL,"%9s "%allo_mb)
    #out_line += colstr(index,WHI,DK_WHI,"size(MB): ")+colstr(index,YEL,DK_YEL,"%9s "%size_mb)
    out_line += colstr(index,WHI,DK_WHI,"frag: ")+colstr(index,YEL,DK_YEL,"%2s "%pool.get_property("fragmentation"))
    
    # get block device names
    #out_line += colstr(index,WHI,DK_WHI,"devices: ")
    #print(dir(pool.children))
    
    print(out_line)
    index += 1
  
###############################################################################

def dict_to_namespace(d):
  """
  Recursively converts a dictionary to a SimpleNamespace object.
  Lists containing dictionaries are also converted.
  """
  if isinstance(d, dict):
    # Convert the dictionary to SimpleNamespace, recursively converting its values
    return SimpleNamespace(**{k: dict_to_namespace(v) for k, v in d.items()})
  elif isinstance(d, list):
    # If the element is a list, recursively convert its items
    return [dict_to_namespace(item) for item in d]
  else:
    # If it's neither a dict nor a list, return the element as is
    return d
  
###############################################################################

def check_mdstat():
  a = mdstat.parse()
  obj = dict_to_namespace(a)
  #print(obj)
  #print(obj.devices)
  index = 0
  for mdev_name in vars(obj.devices):
    #print(mdev_name)
    mdev = getattr(obj.devices, mdev_name)
    #print(mdev)
    out_line = colstr(index,WHI,DK_WHI,"MD.device: ")+colstr(index,YEL,DK_YEL,"%10s "%mdev_name)
    out_line += colstr(index,WHI,DK_WHI,"type: ")+colstr(index,YEL,DK_YEL,"%8s "%mdev.personality)
    #out_line += colstr(index,WHI,DK_WHI,"status: ")+colstr(index,YEL,DK_YEL,"%8s "%mdev.status)
    out_line += colstr(index,WHI,DK_WHI,"disks: ")
    for disk in vars(mdev.disks):
      dname = str(disk)
      #device = Device(dname)
      #status = "OK"
      cmd_line = ["sudo","smartctl","-H","/dev/"+dname]
      cap = command.capture(cmd_line)
      cap_lines = cap.split("\n")
      status = "???"
      for line in cap_lines:  
        #print(line)
        if "self-assessment test result: PASSED" in line:
          status = "PASSED"
        elif "SMART Health Status: OK" in line:
          status = "OK"
        elif "FAIL" in line:
          status = "FAIL"
      
      
      colors = [MAG,DK_MAG]
      if status == "PASSED" or status == "OK":
        colors = [GRN,DK_GRN]
      elif status == "FAIL":
        colors = [RED,DK_RED]
      
      out_line += colstr(index,colors[0],colors[1],"%s "%dname)
      # get freebytes of dname via commandline
      #dev_path = "/dev/"+dname
      #cmdline = ["df", dev_path]
      #out_line += command.Command(cmdline,do_log=True,use_shell=True).exec()
      #print(cap)
      # get smart data
      # get disk status
      # get
      #cmdline = ["sudo","smartctl", "-a", "/dev/"+dname]
      #cap = command.capture(cmdline)
      #out_line += cap
    print(out_line)
    index += 1
  
###############################################################################

def filesystems():
  cmdline = ["df", "-m"]
  cap = command.capture(cmdline)
  index = 0
  
  h1 = "MountPoint"
  h2 = "Device"
  h3 = "Capacity (MiB)"
  h4 = "Used (MiB)"
  h5 = "Avail (MiB)"
  h6 = "Usage %"

  header_str = f"{h1:36} {h2:^28} {h3:>16} {h4:>16} {h5:>16} {h6:>8}"
  print(header_str)

  sorted_lines = {}
  for line in cap.split("\n"):
    if index > 0:
      split_line = line.split()
      if(len(split_line) >= 6):
        key = split_line[5]
        sorted_lines[key] = line
    index += 1  

  sorted_keys = sorted(sorted_lines)
  #print(sorted_lines)
  
  index = 0
  for key in sorted_keys:
    line = sorted_lines[key]
    split_line = line.split()
    
    if(len(split_line) >= 6):
      #print(split_line)
      dev = split_line[0]
      cap = int(split_line[1])
      used = int(split_line[2])
      avail = int(split_line[3])
      percent = split_line[4]
      mount = split_line[5]
      #filesystem = split_line[6]
      cap_str = f"{cap:,}"
      used_str = f"{used:,}"
      avail_str = f"{avail:,}"
      
      percent_as_int = int(percent[:-1])
      percent = f"{percent_as_int}"
      out_line = colstr(index,YEL,DK_YEL,"%-32s "%mount)
      out_line += colstr(index,ORA,DK_ORA,"%32s "%dev)
      out_line += colstr(index,MAG,DK_MAG,"%16s "%cap_str)
      out_line += colstr(index,LBLU,DK_LBLU,"%16s "%used_str)
      out_line += colstr(index,CYN,DK_CYN,"%16s "%avail_str)

      ####################################
      pct_colors = []
      if percent_as_int > 90:
        pct_colors = [RED,DK_RED]
      elif percent_as_int > 80:
        pct_colors = [ORA,DK_ORA]
      elif percent_as_int < 30:
        pct_colors = [GRN,DK_GRN]
      else:
        pct_colors = [YEL,DK_YEL]          
      ####################################

      out_line += colstr(index,pct_colors[0],pct_colors[1],"%8s "%percent)
      #out_line += colstr(index,WHI,DK_WHI,"fs: ")+colstr(index,YEL,DK_YEL,"%-5s "%filesystem)
      
      print(out_line)
    index += 1  

###############################################################################

sepstr("ZFS")
check_zfs()
sepstr("MDSTAT")
check_mdstat()
sepstr("MOUNTS")
filesystems()
sepstr()
