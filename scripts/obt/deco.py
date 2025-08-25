###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, string

###############################################################################

# Color database - RGB values for named colors
COLOR_DB = {
    # Basic ANSI colors
    'black': (0, 0, 0),
    'red': (255, 0, 0),
    'green': (0, 255, 0),
    'yellow': (255, 255, 0),
    'blue': (0, 0, 255),
    'magenta': (255, 0, 255),
    'cyan': (0, 255, 255),
    'white': (255, 255, 255),
    
    # Bright variants
    'brightred': (255, 128, 128),
    'brightgreen': (128, 255, 128),
    'brightblue': (128, 128, 255),
    
    # Extended colors
    'orange': (255, 128, 0),
    'purple': (128, 0, 255),
    'pink': (255, 192, 203),
    
    # Grey levels using dedicated greyscale ramp (232-255) - all 24 levels
    # Each step is +10 in RGB values: grey0=RGB(8,8,8) to grey23=RGB(238,238,238)
    'grey0': 232,    # RGB(8,8,8)
    'grey1': 233,    # RGB(18,18,18)
    'grey2': 234,    # RGB(28,28,28)
    'grey3': 235,    # RGB(38,38,38)
    'grey4': 236,    # RGB(48,48,48)
    'grey5': 237,    # RGB(58,58,58)
    'grey6': 238,    # RGB(68,68,68)
    'grey7': 239,    # RGB(78,78,78)
    'grey8': 240,    # RGB(88,88,88)
    'grey9': 241,    # RGB(98,98,98)
    'grey10': 242,   # RGB(108,108,108)
    'grey11': 243,   # RGB(118,118,118)
    'grey12': 244,   # RGB(128,128,128) - Middle grey
    'grey13': 245,   # RGB(138,138,138)
    'grey14': 246,   # RGB(148,148,148)
    'grey15': 247,   # RGB(158,158,158)
    'grey16': 248,   # RGB(168,168,168)
    'grey17': 249,   # RGB(178,178,178)
    'grey18': 250,   # RGB(188,188,188)
    'grey19': 251,   # RGB(198,198,198)
    'grey20': 252,   # RGB(208,208,208)
    'grey21': 253,   # RGB(218,218,218)
    'grey22': 254,   # RGB(228,228,228)
    'grey23': 255,   # RGB(238,238,238)
    
    # Color shades (0=brightest, 4=darkest)
    # Reds
    'red0': 196,   # bright red
    'red1': 160,   # red
    'red2': 124,   # dark red
    'red3': 88,    # darker red
    'red4': 52,    # darkest red
    
    # Greens
    'grn0': 46,    # bright green
    'grn1': 40,    # lime green
    'grn2': 34,    # green
    'grn3': 28,    # forest green
    'grn4': 22,    # dark green
    
    # Blues
    'blu0': 21,    # bright blue
    'blu1': 20,    # blue
    'blu2': 19,    # navy blue
    'blu3': 18,    # dark blue
    'blu4': 17,    # midnight blue
    
    # AltBlue
    'blx0': 110,   
    'blx1': 67,    
    'blx2': 68,    
    'blx3': 69,    
    'blx4': 62,    

    # Cyans
    'cyn0': 51,    # bright cyan
    'cyn1': 45,    # cyan
    'cyn2': 38,    # teal
    'cyn3': 30,    # dark cyan
    'cyn4': 23,    # darker cyan
    
    # Yellows
    'yel0': 226,   # bright yellow
    'yel1': 220,   # gold
    'yel2': 214,   # orange yellow
    'yel3': 178,   # khaki
    'yel4': 142,   # tan
    
    # Magentas
    'mag0': 201,   # bright magenta
    'mag1': 200,   # magenta
    'mag2': 164,   # purple magenta
    'mag3': 128,   # purple
    'mag4': 91,    # dark magenta
    
    # Oranges
    'ora0': 208,   # bright orange
    'ora1': 202,   # orange
    'ora2': 166,   # dark orange
    'ora3': 130,   # burnt orange
    'ora4': 94,    # brown orange
    
    # Additional color families with 5+ shades
    'pnk0': 218,   # bright pink
    'pnk1': 212,   # medium-bright pink
    'pnk2': 206,   # medium pink
    'pnk3': 200,   # medium-dark pink
    'pnk4': 164,   # dark pink
    
    'pur0': 141,   # bright purple
    'pur1': 135,   # medium-bright purple
    'pur2': 99,    # medium purple
    'pur3': 63,    # medium-dark purple
    'pur4': 54,    # dark purple
    
    'gry0': 255,   # white
    'gry1': 252,   # very light gray
    'gry2': 249,   # light gray
    'gry3': 246,   # medium-light gray
    'gry4': 243,   # medium gray
    'gry5': 240,   # medium-dark gray
    'gry6': 237,   # dark gray
    'gry7': 234,   # very dark gray
    
    'brn0': 215,   # light brown/tan
    'brn1': 179,   # medium-light brown
    'brn2': 137,   # medium brown
    'brn3': 101,   # medium-dark brown
    'brn4': 95,    # dark brown
    
    'teal0': 49,   # bright teal
    'teal1': 43,   # medium-bright teal
    'teal2': 37,   # medium teal
    'teal3': 31,   # medium-dark teal
    'teal4': 23,   # dark teal

    'sata0': 230,   # sat series a
    'sata1': 194,   # sat series a
    'sata2': 195,   # sat series a
    'sata3': 189,   # sat series a
    'sata4': 225,   # sat series a

    'satb0': 187,   # sat series b
    'satb1': 151,   # sat series b
    'satb2': 152,   # sat series b
    'satb3': 146,   # sat series b
    'satb4': 182,   # sat series b
    
    'satc0': 144,   # sat series c
    'satc1': 108,   # sat series c
    'satc2': 109,   # sat series c
    'satc3': 103,   # sat series c
    'satc4': 139,   # sat series c

    'satd0': 101,   # sat series d
    'satd1': 65,   # sat series d
    'satd2': 66,   # sat series d
    'satd3': 60,   # sat series d
    'satd4': 96,   # sat series d

    # Aliases
    'gray': (128, 128, 128),
    'gray0': (32, 32, 32),
    'gray1': (64, 64, 64),
    'gray2': (96, 96, 96),
    'gray3': (128, 128, 128),
    'gray4': (160, 160, 160),
    'gray5': (192, 192, 192),
    'gray6': (224, 224, 224),
    'gray7': (240, 240, 240),
}

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
      rval = "\\[" + rval + "\\]"
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
      rval = "\\["+rval+"\\]"
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
  def red(self,string):
    return self.vrgb256(255,0,0)+str(string)+self.reset()
  def green(self,string):
    return self.vrgb256(0,255,0)+str(string)+self.reset()
  def yellow(self,string):
    return self.vrgb256(255,255,0)+str(string)+self.reset()
  def blue(self,string):
    return self.vrgb256(0,0,255)+str(string)+self.reset()
  def magenta(self,string):
    return self.vrgb256(255,0,255)+str(string)+self.reset()
  def cyan(self,string):
    return self.vrgb256(0,255,255)+str(string)+self.reset()
  def white(self,string):
    return self.vrgb256(255,255,255)+str(string)+self.reset()
  def orange(self,string,blink=False):
    bl = self.blink() if blink else ""
    return self.vrgb256(255,128,0)+bl+str(string)+self.reset()
  ###############################
  def reverseVideo(self,string):
    """Apply reverse video (swap foreground/background colors)"""
    rval = "\033[7m"
    if self.bash:
      rval = "\\[" + rval + "\\]"
    return rval + str(string) + self.reset()
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

class CustomTheme:
    """
    A flexible theme system that allows custom styling for named elements.
    Each element can have foreground color, background color, and text effects.
    """
    
    def __init__(self, name="custom", bash=False):
        self.name = name
        self.bash = bash
        self.styles = {}  # Dictionary of element_name -> style_dict
        
    def add_style(self, element_name, fg=None, bg=None, reverse=False, blink=False, bold=False, dim=False, underline=False):
        """
        Add or update a style for a named element.
        
        Args:
            element_name: Name of the element to style (e.g., 'class_name', 'method_signature')
            fg: Foreground color name from COLOR_DB or RGB tuple or 256-color index
            bg: Background color name from COLOR_DB or RGB tuple or 256-color index
            reverse: Apply reverse video
            blink: Apply blinking effect
            bold: Apply bold effect
            dim: Apply dim effect
            underline: Apply underline effect
        """
        self.styles[element_name] = {
            'fg': fg,
            'bg': bg,
            'reverse': reverse,
            'blink': blink,
            'bold': bold,
            'dim': dim,
            'underline': underline
        }
        
    def _get_color_code(self, color, is_bg=False):
        """Convert a color specification to ANSI escape code."""
        if color is None:
            return ""
            
        # Check if it's a named color in COLOR_DB
        if isinstance(color, str) and color in COLOR_DB:
            color_val = COLOR_DB[color]
            if isinstance(color_val, int):
                # It's a 256-color index (like grey0-grey23)
                if is_bg:
                    return f"\033[48;5;{color_val}m"
                else:
                    return f"\033[38;5;{color_val}m"
            else:
                # It's an RGB tuple
                color = color_val
                
        # Handle direct 256-color index
        if isinstance(color, int):
            if is_bg:
                return f"\033[48;5;{color}m"
            else:
                return f"\033[38;5;{color}m"
                
        # Handle RGB tuple
        if isinstance(color, (list, tuple)) and len(color) == 3:
            r, g, b = color
            # Convert to 256-color approximation
            r = int((r * 5) / 255)
            g = int((g * 5) / 255)
            b = int((b * 5) / 255)
            color_index = 16 + 36 * r + 6 * g + b
            if is_bg:
                return f"\033[48;5;{color_index}m"
            else:
                return f"\033[38;5;{color_index}m"
                
        return ""
        
    def decorate(self, element_name, text):
        """
        Apply the style for the named element to the given text.
        
        Args:
            element_name: Name of the element style to apply
            text: Text to decorate
            
        Returns:
            Decorated text with ANSI escape codes
        """
        if element_name not in self.styles:
            return str(text)  # No style defined, return as-is
            
        style = self.styles[element_name]
        codes = []
        
        # Add text effects
        if style.get('bold'):
            codes.append("\033[1m")
        if style.get('dim'):
            codes.append("\033[2m")
        if style.get('underline'):
            codes.append("\033[4m")
        if style.get('blink'):
            codes.append("\033[5m")
        if style.get('reverse'):
            codes.append("\033[7m")
            
        # Add colors
        fg_code = self._get_color_code(style.get('fg'), is_bg=False)
        if fg_code:
            codes.append(fg_code)
        bg_code = self._get_color_code(style.get('bg'), is_bg=True)
        if bg_code:
            codes.append(bg_code)
            
        if not codes:
            return str(text)
            
        # Apply bash escaping if needed
        prefix = "".join(codes)
        if self.bash:
            prefix = "\\[" + prefix + "\\]"
            
        reset = "\033[m"
        if self.bash:
            reset = "\\[" + reset + "\\]"
            
        return prefix + str(text) + reset
        
    def clone(self):
        """Create a copy of this theme."""
        new_theme = CustomTheme(self.name, self.bash)
        new_theme.styles = self.styles.copy()
        return new_theme

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
  def green(self,string):
    return self._theme.green(string)
  def blue(self,string):
    return self._theme.blue(string)
  def black(self,string):
    return self._theme.black(string) if hasattr(self._theme, 'black') else string
  def gray(self,string):
    return self._theme.gray(string) if hasattr(self._theme, 'gray') else self._theme.rgbstr(128,128,128,string)
  def brightred(self,string):
    return self._theme.brightred(string) if hasattr(self._theme, 'brightred') else self._theme.rgbstr(255,128,128,string)
  def brightgreen(self,string):
    return self._theme.brightgreen(string) if hasattr(self._theme, 'brightgreen') else self._theme.rgbstr(128,255,128,string)
  def brightblue(self,string):
    return self._theme.brightblue(string) if hasattr(self._theme, 'brightblue') else self._theme.rgbstr(128,128,255,string)
  def purple(self,string):
    return self._theme.purple(string) if hasattr(self._theme, 'purple') else self._theme.rgbstr(128,0,255,string)
  def pink(self,string):
    return self._theme.pink(string) if hasattr(self._theme, 'pink') else self._theme.rgbstr(255,192,203,string)
  # Grey levels (0=darkest, 7=lightest)
  def grey0(self,string):  # Near black
    return self._theme.grey0(string) if hasattr(self._theme, 'grey0') else self._theme.rgbstr(32,32,32,string)
  def grey1(self,string):
    return self._theme.grey1(string) if hasattr(self._theme, 'grey1') else self._theme.rgbstr(64,64,64,string)
  def grey2(self,string):
    return self._theme.grey2(string) if hasattr(self._theme, 'grey2') else self._theme.rgbstr(96,96,96,string)
  def grey3(self,string):
    return self._theme.grey3(string) if hasattr(self._theme, 'grey3') else self._theme.rgbstr(128,128,128,string)
  def grey4(self,string):
    return self._theme.grey4(string) if hasattr(self._theme, 'grey4') else self._theme.rgbstr(160,160,160,string)
  def grey5(self,string):
    return self._theme.grey5(string) if hasattr(self._theme, 'grey5') else self._theme.rgbstr(192,192,192,string)
  def grey6(self,string):
    return self._theme.grey6(string) if hasattr(self._theme, 'grey6') else self._theme.rgbstr(224,224,224,string)
  def grey7(self,string):  # Near white
    return self._theme.grey7(string) if hasattr(self._theme, 'grey7') else self._theme.rgbstr(240,240,240,string)
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
  ###############################
  def reverseVideo(self,string):
    return self._theme.reverseVideo(string)
  ###############################
  def fg(self, color):
    """Return ANSI escape sequence for foreground color by name, RGB tuple, or color index"""
    if isinstance(color, str):
      if color in COLOR_DB:
        value = COLOR_DB[color]
        if isinstance(value, int):
          # Direct color index
          return "\033[38;5;%dm" % value
        else:
          # RGB tuple
          r, g, b = value
      else:
        return ""  # Unknown color
    elif isinstance(color, int):
      # Direct color index (0-255)
      return "\033[38;5;%dm" % color
    elif isinstance(color, (tuple, list)) and len(color) == 3:
      r, g, b = color
    else:
      return ""
    
    # Convert RGB to 256 color palette
    r = int((r * 5) / 255)
    g = int((g * 5) / 255)
    b = int((b * 5) / 255)
    color_code = 16 + 36 * r + 6 * g + b
    return "\033[38;5;%dm" % color_code
  ###############################
  def bg(self, color):
    """Return ANSI escape sequence for background color by name, RGB tuple, or color index"""
    if isinstance(color, str):
      if color in COLOR_DB:
        value = COLOR_DB[color]
        if isinstance(value, int):
          # Direct color index
          return "\033[48;5;%dm" % value
        else:
          # RGB tuple
          r, g, b = value
      else:
        return ""  # Unknown color
    elif isinstance(color, int):
      # Direct color index (0-255)
      return "\033[48;5;%dm" % color
    elif isinstance(color, (tuple, list)) and len(color) == 3:
      r, g, b = color
    else:
      return ""
    
    # Convert RGB to 256 color palette
    r = int((r * 5) / 255)
    g = int((g * 5) / 255)
    b = int((b * 5) / 255)
    color_code = 16 + 36 * r + 6 * g + b
    return "\033[48;5;%dm" % color_code
  ###############################
  def reset(self):
    """Return ANSI reset sequence"""
    return "\033[m"
  ###############################
  def strip_ansi(self, text):
    """Remove ANSI escape sequences from text to get visible length"""
    import re
    ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    return ansi_escape.sub('', text)
  ###############################
  def visible_len(self, text):
    """Get the visible length of text (excluding ANSI codes)"""
    return len(self.strip_ansi(text))
  ###############################
  def formatColumns(self, column_configs, column_texts):
    """
    Format text into aligned columns, handling ANSI escape codes properly.
    
    Args:
      column_configs: List of tuples (width, alignment) where:
        - width: int or None (None means no padding)
        - alignment: 'left', 'right', or 'center'
      column_texts: List of strings (may contain ANSI codes)
    
    Returns:
      Formatted string with proper column alignment
    """
    formatted_cols = []
    
    for i, (text, config) in enumerate(zip(column_texts, column_configs)):
      if config is None or len(config) < 1:
        # No formatting for this column
        formatted_cols.append(text)
        continue
      
      width = config[0] if len(config) > 0 else None
      align = config[1] if len(config) > 1 else 'left'
      
      if width is None:
        # No width specified, just use the text as-is
        formatted_cols.append(text)
      else:
        # Calculate visible length and padding needed
        visible_length = self.visible_len(text)
        padding_needed = width - visible_length
        
        if padding_needed <= 0:
          # Text is already longer than width, just use it
          formatted_cols.append(text)
        else:
          # Apply alignment with proper padding
          if align == 'right':
            formatted_cols.append(' ' * padding_needed + text)
          elif align == 'center':
            left_pad = padding_needed // 2
            right_pad = padding_needed - left_pad
            formatted_cols.append(' ' * left_pad + text + ' ' * right_pad)
          else:  # left
            formatted_cols.append(text + ' ' * padding_needed)
    
    return ''.join(formatted_cols)

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
