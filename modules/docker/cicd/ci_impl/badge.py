#!/usr/bin/env python3

import cairo, math, os, time, jinja2
from orkbb import BranchStatus

w = 300
h = 300

TEMPLATETEXT = """
<svg xmlns="http://www.w3.org/2000/svg" width="{{ left.width + right.width }}" height="18">
  <linearGradient id="smooth" x2="0" y2="100%">
    <stop offset="0"  stop-color="#fff" stop-opacity=".7"/>
    <stop offset=".1" stop-color="#aaa" stop-opacity=".1"/>
    <stop offset=".9" stop-color="#000" stop-opacity=".3"/>
    <stop offset="1"  stop-color="#000" stop-opacity=".5"/>
  </linearGradient>
  <rect rx="4" width="{{ left.width + right.width }}" height="18" fill="{{ left.color }}"/>
  <rect rx="4" x="{{ left.width }}" width="{{ right.width }}" height="18" fill="{{ right.color }}"/>
  <rect x="{{ left.width }}" width="4" height="18" fill="{{ right.color }}"/>
  <rect rx="4" width="{{ left.width+right.width }}" height="18" fill="url(#smooth)"/>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="{{ left.width/2+1 }}" y="14" fill="#010101" fill-opacity=".3">{{ left.text }}</text>
    <text x="{{ left.width/2+1 }}" y="13">{{ left.text }}</text>
    <text x="{{ left.width+right.width/2-1 }}" y="14" fill="#010101" fill-opacity=".3">{{ right.text }}</text>
    <text x="{{ left.width+right.width/2-1 }}" y="13">{{ right.text }}</text>
  </g>
</svg>
"""

def load_template(name):
  return TEMPLATETEXT

env = jinja2.Environment(
    loader=jinja2.FunctionLoader(load_template),
    autoescape=jinja2.select_autoescape(['html', 'xml'])
)
template = env.get_template('index.html')


surface = cairo.SVGSurface("dummy.svg", w, h)
context = cairo.Context(surface)
context.select_font_face("Graph", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
context.set_font_size(16)

def _create(outpath = None,
            left_text=None,
            left_color=None,
            right_text=None,
            right_color=None ):

 left = {
        "color": left_color,
        "text": left_text,
        "width": context.text_extents(left_text).width
 }
 right = {
        "color": right_color,
        "text": right_text,
        "width": context.text_extents(right_text).width
 }

 template = env.get_template("yo")
 output = template.render(left=left, right=right)
 with open(outpath,"w") as f:
   f.write(output)


################################################################################

class Data:
  #######################################################################
  def __init__(self):
    self._leftcolor = "#202040"
    self._rightcolor = "#000000"
    self._lefttext = "BuildStatus"
    self._righttext = "???"
    self._outpath = "???"
  #######################################################################
  def create(self):
    _create( outpath=self._outpath,
             left_text=self._lefttext,right_text=self._righttext,
             left_color=self._leftcolor,right_color=self._rightcolor)
  #######################################################################
  def updateStatus(self,curstatus,prvstatus):
     ##################################
     # set text
     ##################################
     if curstatus==BranchStatus.PASSED:
       self._righttext = "PASSED"
     elif curstatus==BranchStatus.FAILED:
       self._righttext = "FAILED"
     elif curstatus==BranchStatus.INIT:
       self._righttext = "INIT"
     elif curstatus==BranchStatus.BUILDING:
       self._righttext = "BUILDING"
     else:
       self._righttext = "????"
     ##################################
     # set color
     ##################################
     self._rightcolor = "#000000"
     if curstatus==BranchStatus.PASSED:
       self._rightcolor = "#006000"
     elif curstatus==BranchStatus.FAILED:
       self._rightcolor = "#500000"
     elif curstatus==BranchStatus.INIT:
       self._rightcolor = "#000000"
     elif curstatus==BranchStatus.BUILDING:
       if prvstatus==BranchStatus.PASSED:
         self._rightcolor = "#006000"
       elif prvstatus==BranchStatus.FAILED:
         self._rightcolor = "#500000"
       elif prvstatus==BranchStatus.INIT:
         self._rightcolor = "#404040"
