import ork.command

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

    ork.command.run(["obt_litex_env.py",
                    "--cpu",cpu,
                    "--platform",platform,
                    "--target",target,
                    "--exec", cmdlist ])