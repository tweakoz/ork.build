from enum import Enum
import pint, math
import numpy as np
from scipy.interpolate import UnivariateSpline

#####################################################
# base units
#####################################################

units = pint.UnitRegistry() 
Q_ = units.Quantity

units.define('TE = [teeth]')
units.define('R = [rotations]')

#####################################################

meter = units.meter
mm = units.mm
feet = units.ft
inch = units.inch
second = units.second
minute = units.minute
teeth = units.TE 
rotations = units.R 

#####################################################

class MillDirection(Enum):
  CLOCKWISE = 1
  COUNTER_CLOCKWISE = 2

#####################################################

class EndMill:
  def __init__(self, numflutes=2, diameter=(1/8)*inch):
    self._numflutes = numflutes
    self._diameter = diameter
  def __str__(self):
    return "EndMill diameter<%s> numflutes<%s>" % (self._diameter,self._numflutes)

#####################################################

class Material:
  def __init__(self,name, cutspeed):
    self._name = name
    self._cutspeed = cutspeed
    self._tfsamples = dict()

  def addToothFeedSample(self,endmill_diameter,mm_per_tooth_per_rotation):
    self._tfsamples[endmill_diameter.to("mm")] = mm_per_tooth_per_rotation.to("mm/TE")

  def extrapolate(self,d):
    npa = np.zeros((len(self._tfsamples),2))
    i = 0
    for k in self._tfsamples.keys():
      v = self._tfsamples[k]
      npa[i,:] = [k.magnitude,v.magnitude]
      i+=1
    dataset_k, dataset_v = npa.T
    extrapolator = UnivariateSpline( dataset_k, dataset_v )
    y = extrapolator( d.magnitude )
    return y * d.units

  def __str__(self):
    rv = "name<%s> cutspeed<%s>" % (self._name,self._cutspeed)
    return rv

#####################################################

class SoftWood(Material):
  def __init__(self):
    super().__init__("SoftWood",500*meter/minute)
    self.addToothFeedSample( 0.5*mm, .010 * mm / teeth )
    self.addToothFeedSample( 1.0*mm, .012 * mm / teeth )
    self.addToothFeedSample( 1.5*mm, .015 * mm / teeth )
    self.addToothFeedSample( 2.0*mm, .020 * mm / teeth )
    self.addToothFeedSample( 2.5*mm, .025 * mm / teeth )
    self.addToothFeedSample( 3.0*mm, .030 * mm / teeth )

class HardWood(Material):
  def __init__(self):
    super().__init__("HardWood",450*meter/minute)
    self.addToothFeedSample( 0.5*mm, .008 * mm / teeth )
    self.addToothFeedSample( 1.0*mm, .010 * mm / teeth )
    self.addToothFeedSample( 1.5*mm, .012 * mm / teeth )
    self.addToothFeedSample( 2.0*mm, .015 * mm / teeth )
    self.addToothFeedSample( 2.5*mm, .018 * mm / teeth )
    self.addToothFeedSample( 3.0*mm, .020 * mm / teeth )

class MDF(Material):
  def __init__(self):
    super().__init__("MDF",450*meter/minute)
    self.addToothFeedSample( 0.5*mm, .010 * mm / teeth )
    self.addToothFeedSample( 1.0*mm, .012 * mm / teeth )
    self.addToothFeedSample( 1.5*mm, .015 * mm / teeth )
    self.addToothFeedSample( 2.0*mm, .017 * mm / teeth )
    self.addToothFeedSample( 2.5*mm, .020 * mm / teeth )
    self.addToothFeedSample( 3.0*mm, .025 * mm / teeth )

class Brass(Material):
  def __init__(self):
    super().__init__("Brass",360*meter/minute)
    self.addToothFeedSample( 0.5*mm, .003 * mm / teeth )
    self.addToothFeedSample( 1.0*mm, .004 * mm / teeth )
    self.addToothFeedSample( 1.5*mm, .006 * mm / teeth )
    self.addToothFeedSample( 2.0*mm, .008 * mm / teeth )
    self.addToothFeedSample( 2.5*mm, .012 * mm / teeth )
    self.addToothFeedSample( 3.0*mm, .015 * mm / teeth )

class Bronze(Material):
  def __init__(self):
    super().__init__("Bronze",360*meter/minute)
    self.addToothFeedSample( 0.5*mm, .003 * mm / teeth )
    self.addToothFeedSample( 1.0*mm, .004 * mm / teeth )
    self.addToothFeedSample( 1.5*mm, .006 * mm / teeth )
    self.addToothFeedSample( 2.0*mm, .008 * mm / teeth )
    self.addToothFeedSample( 2.5*mm, .012 * mm / teeth )
    self.addToothFeedSample( 3.0*mm, .015 * mm / teeth )

class Copper(Material):
  def __init__(self):
    super().__init__("Copper",360*meter/minute)
    self.addToothFeedSample( 0.5*mm, .003 * mm / teeth )
    self.addToothFeedSample( 1.0*mm, .004 * mm / teeth )
    self.addToothFeedSample( 1.5*mm, .006 * mm / teeth )
    self.addToothFeedSample( 2.0*mm, .008 * mm / teeth )
    self.addToothFeedSample( 2.5*mm, .012 * mm / teeth )
    self.addToothFeedSample( 3.0*mm, .015 * mm / teeth )

class WroughtAluminum(Material):
  def __init__(self):
    super().__init__("WroughtAluminum",300*meter/minute)
    self.addToothFeedSample( 0.5*mm, .003 * mm / teeth )
    self.addToothFeedSample( 1.0*mm, .004 * mm / teeth )
    self.addToothFeedSample( 1.5*mm, .006 * mm / teeth )
    self.addToothFeedSample( 2.0*mm, .008 * mm / teeth )
    self.addToothFeedSample( 2.5*mm, .012 * mm / teeth )
    self.addToothFeedSample( 3.0*mm, .016 * mm / teeth )

class CastAluminum(Material):
  def __init__(self):
    super().__init__("CastAluminum",200*meter/minute)
    self.addToothFeedSample( 0.5*mm, .002 * mm / teeth )
    self.addToothFeedSample( 1.0*mm, .003 * mm / teeth )
    self.addToothFeedSample( 1.5*mm, .005 * mm / teeth )
    self.addToothFeedSample( 2.0*mm, .007 * mm / teeth )
    self.addToothFeedSample( 2.5*mm, .011 * mm / teeth )
    self.addToothFeedSample( 3.0*mm, .015 * mm / teeth )

class Steel(Material):
  def __init__(self):
    super().__init__("Steel",90*meter/minute)
    self.addToothFeedSample( 0.5*mm, .001 * mm / teeth )
    self.addToothFeedSample( 1.0*mm, .003 * mm / teeth )
    self.addToothFeedSample( 1.5*mm, .004 * mm / teeth )
    self.addToothFeedSample( 2.0*mm, .006 * mm / teeth )
    self.addToothFeedSample( 2.5*mm, .008 * mm / teeth )
    self.addToothFeedSample( 3.0*mm, .010 * mm / teeth )

#####################################################

def compute_feed(material=None, endmill=None, RPM=None):
  cut_speed = material._cutspeed
  #RPM = cut_speed.to("mm/minute") / (math.pi*endmill._diameter.to("mm"))
  f_z = material.extrapolate(endmill._diameter.to("mm"))
  return (RPM * endmill._numflutes * f_z)/rotations

#####################################################

def compute_rpm(material=None, endmill=None, feed=None):
  cut_speed = material._cutspeed
  f_z = material.extrapolate(endmill._diameter.to("mm"))
  # feed = ((RPM/rotations) * (endmill._numflutes) * f_z)
  # feed = (RPM * endmill._numflutes * f_z)/rotations
  # feed*rotations = RPM * endmill._numflutes * f_z
  # (feed*rotations)/(endmill._numflutes * f_z) = RPM
  rpm = (feed * rotations) / (endmill._numflutes * f_z)
  return rpm.to("R/minute")

#####################################################
def test():
  m  = MDF()
  #####################################################
  em = EndMill( numflutes=2, diameter=(1/8)*inch )
  #####################################################
  RPM = 6000 * rotations / minute
  #####################################################

  a = compute_feed( material = m, 
                    endmill = em,
                    RPM = RPM )

  print("##############################################################")
  print(" mtl : %s\n  em : %s\n RPM : %s\nfeed : %s (linear)" % (m,em,RPM,a))
  print("##############################################################")
  print(" mtl : %s\n  em : %s\n RPM : %s\nfeed : %s (linear)" % (m,em,RPM,a.to(meter/second)))
  print("##############################################################")
  print(" mtl : %s\n  em : %s\n RPM : %s\nfeed : %s (linear)" % (m,em,RPM,a.to(feet/minute)))
  print("##############################################################")

  feed = 1*feet/minute
  RPM = compute_rpm( material=m, endmill=em, feed=feed )
  print(" mtl : %s\n  em : %s\nfeed : %s (linear)\n RPM : %s\n" % (m,em,feed,RPM))
