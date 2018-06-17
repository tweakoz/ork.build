###############################################################################

class deco:
  
  ###############################
  def __init__(self,bash=False):
    self.bash = bash
  ###############################
  def rgb256(self,r,g,b):
    r = int((r*5)/255)
    g = int((g*5)/255)
    b = int((b*5)/255)
    color = 16 + 36 * r + 6 * g + b
    rval = "\033[38;5;%dm" % color
    if self.bash:
      rval = "\[" + rval + "\]"
    return rval
  ###############################
  def reset(self):
    rval = "\033[m"
    if self.bash:
      rval = "\["+rval+"\]"
    return rval
  ###############################
  def magenta(self,string):
    return self.rgb256(255,0,255)+str(string)+self.reset()
  def cyan(self,string):
    return self.rgb256(0,255,255)+str(string)+self.reset()
  def white(self,string):
    return self.rgb256(255,255,255)+str(string)+self.reset()
  def orange(self,string):
    return self.rgb256(255,128,0)+str(string)+self.reset()
  def yellow(self,string):
    return self.rgb256(255,255,0)+str(string)+self.reset()
  def red(self,string):
    return self.rgb256(255,0,0)+str(string)+self.reset()
  ###############################
  def key(self,string):
    return self.rgb256(255,255,0)+str(string)+self.reset()
  def val(self,string):
    return self.rgb256(255,255,255)+str(string)+self.reset()
  def path(self,string):
    return self.rgb256(255,255,128)+str(string)+self.reset()
  def inf(self,string):
    return self.rgb256(128,128,255)+str(string)+self.reset()
  def warn(self,string):
    return self.yellow(string)+self.reset()
  def err(self,string):
    return self.red(string)+self.reset()
  ###############################

__all__ =	[ "deco" ]
