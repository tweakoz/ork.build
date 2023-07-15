import obt.command

def shell(cmdlist=None,cpu=None,platform=None,target=None,triple=None):
  if triple!=None:
      cpu = triple["cpu"]
      platform = triple["platform"]
      target = triple["target"]
      obt.command.run(["obt.litex.env.py",
                       "--cpu",cpu,
                       "--platform",platform,
                       "--target",target,
                       "--shell"])

def run(cmdlist=None,cpu=None,platform=None,target=None,triple=None):
  if triple!=None:
      cpu = triple["cpu"]
      platform = triple["platform"]
      target = triple["target"]

  if isinstance(cmdlist,list):
    tmplist = []
    for item in cmdlist:
      tmplist.append(str(item))
    cmdlist = " ".join(tmplist)

    obt.command.run(["obt.litex.env.py",
                    "--cpu",cpu,
                    "--platform",platform,
                    "--target",target,
                    "--exec", cmdlist ])
