from obt import command

def prefix_for_package(pkg):
  cmdlist = ["brew","--prefix",pkg]
  return command.capture(cmdlist).replace("\n","")
