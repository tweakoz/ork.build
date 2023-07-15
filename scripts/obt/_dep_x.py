import obt._dep_enumerate
import obt._dep_node
from obt.deco import Deco 
import sys

deco = Deco()

###############################################################################
def instance(named,with_overrides=True):
  n = obt._dep_node.DepNode.nodeForName(named,with_overrides)
  if n and hasattr(n,"instance") and n.instance.supports_host:
    return n.instance
  return None
###############################################################################
def module_class(named,with_overrides=True):
  n = obt._dep_node.DepNode.nodeForName(named,with_overrides)
  if n and hasattr(n,"module_class") and n.instance.supports_host:
    return n.module_class
  return None
###############################################################################
class Chain:
  ############################
  def __init__(self,named_or_list):
    self._list = list()
    self._dict = dict()
    ##########################
    index = 0
    indexed = dict()
    def visit_provider(provider):
      assert(hasattr(provider,"_name"))
      #print(provider._name)
      nonlocal self, index
      ############################
      # new item ?
      ############################
      if provider._name not in self._dict.keys():
        self._dict[provider._name] = provider
        provider._topoindex = index
        indexed[index] = provider
        index+=1
      ############################
      # recurse into children
      ############################
      for name in provider._required_deps.keys():
        inst = provider._required_deps[name]
        if inst != None:
          visit_provider(inst)
    ##########################
    def perform_on_node(named):
      ##########################
      # check node comformity
      ##########################
      root = obt._dep_node.DepNode.nodeForName(named)
      #print(root)
      if (root==None):
        print(deco.err("DepNode<%s> does not have instance - check that the provider/class is named correctly!"%named))
        sys.exit(-1)
      if (root!=None) and (not hasattr(root,"instance")):
        print(deco.err("DepNode<%s> does not have instance - check that the provider/class is named correctly!"%named))
        sys.exit(-1)
      ##########################
      if root.instance!=None:
        visit_provider(root.instance)
    ##########################
    # start recursion at root
    if isinstance(named_or_list,str):
      perform_on_node(named_or_list)
    elif isinstance(named_or_list,list):
      for item in named_or_list:
        perform_on_node(item)
    ##########################
    # topological unsorted
    ##########################
    topo_unsorted = dict()
    for index in indexed.keys():
      topo_unsorted[index] = set()
      p = indexed[index]
      #print(p)
      deps = p._required_deps
      for d in deps.keys():
        inst = deps[d]
        if inst != None:
          topo_unsorted[index].add(inst._topoindex)
    #print(topo_unsorted)
    ##########################
    # topological sorted
    ##########################
    from toposort import toposort, toposort_flatten
    #print("sorted:")
    sorted = list(toposort_flatten(topo_unsorted))
    #print(sorted)
    for i in reversed(sorted):
      n = indexed[i]
      #print(i,n._name)
      self._list.append(n)
      self._dict[n._name]=n
      #if i._name not in self._dict.keys():
       #self._dict[i._name] = i
       #self._list.append(i)
    ##########################
  
