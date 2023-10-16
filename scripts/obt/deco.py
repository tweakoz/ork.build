###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, string

###############################################################################

class Theme:
  def __init__(self,bash):
    super().__init__()
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
  def blink(self):
    return "\033[5m"
  ###############################
  def vrgb256(self,r,g,b):
    return self.rgb256(r,g,b)
  ###############################
  def rgbstr(self,r,g,b,string):
    return self.rgb256(r,g,b)+str(string)+self.reset()
  ###############################
  def reset(self):
    rval = "\033[m"
    if self.bash:
      rval = "\["+rval+"\]"
    return rval
  ###############################
  def key(self,string):
    return self.vrgb256(255,255,0)+str(string)+self.reset()
  def val(self,string):
    return self.vrgb256(255,255,255)+str(string)+self.reset()
  def path(self,string):
    return self.vrgb256(255,255,128)+str(string)+self.reset()
  def inf(self,string):
    return self.vrgb256(128,128,255)+str(string)+self.reset()
  def warn(self,string):
    return self.yellow(string)+self.reset()
  def err(self,string):
    return self.red(string)+self.reset()
  ###############################
  def bright(self,string):
    return self.vrgb256(255,255,255)+str(string)+self.reset()
  ###############################
  def magenta(self,string):
    return self.vrgb256(255,0,255)+str(string)+self.reset()
  def cyan(self,string):
    return self.vrgb256(0,255,255)+str(string)+self.reset()
  def white(self,string):
    return self.vrgb256(255,255,255)+str(string)+self.reset()
  def orange(self,string,blink=False):
    bl = self.blink() if blink else ""
    return self.vrgb256(255,128,0)+bl+str(string)+self.reset()
  def yellow(self,string):
    return self.vrgb256(255,255,0)+str(string)+self.reset()
  def red(self,string):
    return self.vrgb256(255,0,0)+str(string)+self.reset()
  ###############################
  def promptL(self,string):
    return self.vrgb256(255,0,0)+str(string)+self.reset()
  ###############################
  def promptC(self,string):
    return self.vrgb256(255,255,0)+str(string)+self.reset()
  ###############################
  def promptR(self,string):
    return self.vrgb256(255,128,0)+str(string)+self.reset()
  ###############################

###############################################################################

class DarkTheme(Theme):
  def __init__(self,bash=False):
    super().__init__(bash=bash)
  ###############################
  def val(self,string):
    return self.vrgb256(255,192,192)+str(string)+self.reset()
  ###############################
  def bright(self,string):
    return self.vrgb256(255,255,128)+str(string)+self.reset()

###############################################################################

class InverseTheme(Theme):
  def __init__(self,bash=False):
    super().__init__(bash=bash)
  ###############################
  def vrgb256(self,r,g,b):
    return self.rgb256(255-r,255-g,255-b)
  ###############################
  def promptL(self,string):
    return self.rgb256(255,0,0)+str(string)+self.reset()
  ###############################
  def promptC(self,string):
    return self.rgb256(255,255,0)+str(string)+self.reset()
  ###############################
  def promptR(self,string):
    return self.rgb256(255,128,0)+str(string)+self.reset()
  #def rgbstr(self,r,g,b,string):
  #  return super().rgb256(255-r,255-g,255-b)+str(string)+self.reset()

###############################################################################

class LightTheme(Theme):
  def __init__(self,bash=False):
    super().__init__(bash=bash)
  ###############################
  def key(self,string):
    return self.rgb256(25,25,0)+str(string)+self.reset()
  def val(self,string):
    return self.rgb256(0,160,160)+str(string)+self.reset()
  def path(self,string):
    return self.rgb256(65,65,65)+str(string)+self.reset()
  def inf(self,string):
    return self.rgb256(15,15,30)+str(string)+self.reset()
  def warn(self,string):
    return self.yellow(string)+self.reset()
  def err(self,string):
    return self.red(string)+self.reset()
  ###############################
  def bright(self,string):
    return self.rgb256(0,0,0)+str(string)+self.reset()
  ###############################
  def vrgb256(self,r,g,b):
    return self.rgb256(255-r,255-g,255-b)
  ###############################
  def promptL(self,string):
    return self.rgb256(128,0,0)+str(string)+self.reset()
  ###############################
  def promptC(self,string):
    return self.rgb256(128,128,0)+str(string)+self.reset()
  ###############################
  def promptR(self,string):
    return self.rgb256(128,96,0)+str(string)+self.reset()

###############################################################################

class MonoTheme(Theme):
  def __init__(self,bash=False):
    super().__init__(bash=bash)
  ###############################
  def rgb256(self,r,g,b):
    return ""
  ###############################
  def reset(self):
    return ""

###############################################################################

class Deco:
  
  ###############################
  def __init__(self,bash=False):
    if "OBT_THEME" in os.environ:
      if os.environ["OBT_THEME"]=="dark":
        self._theme = DarkTheme(bash=bash)
      elif os.environ["OBT_THEME"]=="light":
        self._theme = LightTheme(bash=bash)
      elif os.environ["OBT_THEME"]=="inverse":
        self._theme = InverseTheme(bash=bash)
      elif os.environ["OBT_THEME"]=="mono":
        self._theme = MonoTheme(bash=bash)
    else:
      self._theme = DarkTheme(bash=bash)
  ###############################
  def rgbstr(self,r,g,b,string):
    return self._theme.rgbstr(r,g,b,string)
  ###############################
  def magenta(self,string):
    return self._theme.magenta(string)
  def cyan(self,string):
    return self._theme.cyan(string)
  def white(self,string):
    return self._theme.white(string)
  def orange(self,string,blink=False):
    return self._theme.orange(string,blink=blink)
  def yellow(self,string):
    return self._theme.yellow(string)
  def red(self,string):
    return self._theme.red(string)
  ###############################
  def key(self,string):
    return self._theme.key(string)
  def val(self,string):
    return self._theme.val(string)
  def path(self,string):
    return self._theme.path(string)
  def inf(self,string):
    return self._theme.inf(string)
  def warn(self,string):
    return self._theme.warn(string)
  def err(self,string):
    return self._theme.err(string)
  ###############################
  def bright(self,string):
    return self._theme.bright(string)
  ###############################
  def promptL(self,string):
    return self._theme.promptL(string)
  ###############################
  def promptC(self,string):
    return self._theme.promptC(string)
  ###############################
  def promptR(self,string):
    return self._theme.promptR(string)

###############################################################################

class DecoFormatter(string.Formatter):
  def __init__(self):
    self.deco = Deco()    
  def format_field(self, value, format_spec):
    if isinstance(value, str):
      if format_spec.endswith('red'):
        value = self.deco.red(value)
        format_spec = format_spec[:-3]
    return super(DecoFormatter, self).format(value, format_spec)

###############################################################################

__all__ =	[ "deco" ]
