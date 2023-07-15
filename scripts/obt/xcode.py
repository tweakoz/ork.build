import obt.command 

IOS_VERSION = "iphoneos15.2" # latest supported by both bigsur and monterey/x86_64 and M1

_macsdkstr = None
_iossdkstr = None



def macsdkstr():
  global _macsdkstr
  if _macsdkstr==None:
    _macsdkstr = obt.command.capture([
     "xcodebuild",
     "-version",
     "-sdk", "macosx",
     "Path"],do_log=False).splitlines()
  return _macsdkstr

def iossdkstr():
  global _iossdkstr
  if _iossdkstr==None:
    _iossdkstr = obt.command.capture([
     "xcodebuild",
     "-version",
     "-sdk", IOS_VERSION,
     "Path"],do_log=False).splitlines()
  return _iossdkstr
