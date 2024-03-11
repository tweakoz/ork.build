  
###############################################################################

class project:

  #####################

  def __init__(self,named):
    self.name = named
    self.depends = []
    self.sources = []

  #####################

  def add_src(self,src):
    self.sources.append(src)

  #####################

  def dependsOn(self,project):
    self.depends.append(project)

  #####################
  
  def __repr__(self):
    return f"project({self.name})"
  
###############################################################################

class executable(project):
  def __init__(self,named):
    super().__init__(named)

  def emit(self):
    rval = []
    out_str = "add_executable(%s " % (self.name)
    for src in self.sources:
      out_str += src + " "
    out_str += ")"
    rval += [out_str]
    return rval

class sharedLibrary(project):
  def __init__(self,named):
    super().__init__(named)
  def emit(self):
    rval = []
    out_str = "add_library(%s SHARED " % (self.name)
    for src in self.sources:
      out_str += src + " "
    out_str += ")"
    rval += [out_str]
    return rval

###############################################################################

class emitter:
  def __init__(self, platform):
    self.platform = platform
    self.is_ios = "ios" in platform
    self.is_android = "android" in platform
  
###############################################################################

class libref:
  def __init__(self, named, REQUIRED=True, CONFIG=False):
    self.name = named
    self.required = REQUIRED
    self.config = CONFIG
    
  def emit(self):
    if self.required:
      return ['find_library(%s %s REQUIRED)' % (self.name,self.name)]
    else:
      return ['find_library(%s %s)' % (self.name,self.name)]
  
class pkgref:
  def __init__(self, named, REQUIRED=True, CONFIG=False, COMPONENTS=[]):
    self.name = named
    self.required = REQUIRED
    self.config = CONFIG
    self.components = COMPONENTS

  def emit(self):

    out_str = "find_package( " + self.name + " "
    if self.config:
      out_str += "CONFIG "
    if self.required:
      out_str += "REQUIRED "
    if len(self.components) > 0:
      out_str += "COMPONENTS "
      out_str += " ".join(self.components)
      
    out_str += ")"

    return [out_str]
###############################################################################
  
class workspace:

  #####################

  def __init__(self, named):
    self.name = named
    self.projects = dict()
    self.librefs = dict()
    self.pkgrefs = dict()
    self.vars = dict()
    pass

  #####################

  def findLibrary(self, named, REQUIRED=True, CONFIG=False):
    lref = libref(named,REQUIRED,CONFIG)
    self.librefs[named] = lref

  #####################

  def findPackage(self, named, #
                        REQUIRED=True, #
                        CONFIG=False, #
                        COMPONENTS=[]): #

    lref = pkgref(named, #
                  REQUIRED=REQUIRED, #
                  CONFIG=CONFIG, #
                  COMPONENTS=COMPONENTS)

    self.pkgrefs[named] = lref

  #####################

  def setVar(self, named, value):
    self.vars[named] = value

  #####################

  def createExecutable(self,named):
    p = executable(named)
    self.projects[named] = p
    return p
  
  def createSharedLibrary(self,named):
    p = sharedLibrary(named)
    self.projects[named] = p
    return p

  #####################

  def toposort(self):
    # topological sort of projects based on dependencies

    # 1. recursive function to visit a node, add to dictionary with depth as key
    # 2. sort the dictionary by depth
    # 3. return the reverse sorted list of projects (highest depths first)

    def visit(node,depth,visited,sorted):
      if node in visited:
        return
      visited.add(node)
      for dep in node.depends:
        visit(dep,depth+1,visited,sorted)
      if depth not in sorted:
        sorted[depth] = []
      sorted[depth].append(node)
      
    visited = set()
    sorted = dict()
    for p in self.projects.values():
      visit(p,0,visited,sorted)
      
    the_sorted = []
    for d in sorted.keys():
      the_sorted.extend(sorted[d])
      
    return the_sorted

  #####################

  def emit(self, emit_ctx):
    sorted = self.toposort()
    print(sorted)
    
    self.top_cmlist = []
    self.top_cmlist += ["cmake_minimum_required(VERSION 3.28.3)"]
    self.top_cmlist += ["set(CMAKE_CXX_STANDARD 20)"]
    self.top_cmlist += ["set(CMAKE_CXX_STANDARD_REQUIRED ON)"]
    self.top_cmlist += ["set(CMAKE_CXX_EXTENSIONS OFF)"]
    self.top_cmlist += ["project("+self.name+" LANGUAGES CXX OBJCXX)"]
    
    if emit_ctx.is_ios:
      #
      self.top_cmlist += ['set(CMAKE_OSX_SYSROOT %s CACHE PATH "The iOS SDK sysroot")']
      self.top_cmlist += ['include(${CMAKE_CURRENT_SOURCE_DIR}/../../ios.toolchain.cmake)']
      self.top_cmlist += ['include(${CMAKE_CURRENT_SOURCE_DIR}/conan_toolchain.cmake)']

    for k in self.librefs:
      lref = self.librefs[k]
      self.top_cmlist += lref.emit()
        
    for k in self.pkgrefs:
      pref = self.pkgrefs[k]
      self.top_cmlist += pref.emit()

    for k in self.vars:
      self.top_cmlist += ["set(%s %s)" % (k,self.vars[k])]
    
    for p in sorted:
      self.top_cmlist += p.emit()
      
    out_str = "\n".join(self.top_cmlist)
    print(out_str)
  