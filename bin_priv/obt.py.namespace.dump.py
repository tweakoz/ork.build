#!/usr/bin/env python3 

import argparse, importlib, pkgutil, sys, pathlib, ast
from obt.deco import Deco 

deco = Deco() 

parser = argparse.ArgumentParser(description='Enumerate the contents of a namespace package')
parser.add_argument('ns_name', type=str, help='The name of the namespace package to enumerate')
args = parser.parse_args()

###############################################################################

module_colors = [ # blue
  (64,64,128),
  (192,192,224),
  (224,224,255)
]
package_colors = [ # green
  (64,128,64),
  (192,224,192),
  (224,255,224)
]
method_colors = [ # magenta
  (128,64,128),
  (224,192,224),
  (255,224,255)
]
function_colors = [ # yellow-green
  (128,128,64),
  (224,224,192),
  (255,255,224)
]
class_colors = [ # cyan
  (64,128,128),
  (192,224,224),
  (224,255,255)
]

###############################################################################

def iterate_module_contents(item_path : pathlib.Path, level: int):
  indent = '  ' * level
  short_name = item_path.parts[-1]
  mod_color = module_colors[level]
  colored_mod = deco.rgbstr(*mod_color, short_name)
  colored_state = deco.yellow('module')
  print(f'{indent}{colored_mod} : {colored_state}')
  # enumerate the contents of the module (without importing it)
  # this is done by reading the file and looking for methods
  # we can use the ast module to parse the file
  # and extract the methods
  # for now, we just print the methods and classes
  #print(item_path)
  dot_py = item_path.with_suffix('.py')
  visited_functions = set()
  if dot_py.exists() and dot_py.is_file():
    the_ast = ast.parse(open(dot_py).read())
    # first walk classes, and their methods (recusively)
    for node in ast.walk(the_ast):
      is_class = isinstance(node, ast.ClassDef)
      if is_class:
        class_name = node.name
        class_color = class_colors[level]
        colored_class = deco.rgbstr(*class_color, class_name)
        colored_state = deco.yellow('class')
        print(f'{indent}  {colored_class} : {colored_state}')
        for node in ast.walk(node):
          is_function = isinstance(node, ast.FunctionDef)
          if is_function:
            visited_functions.add(node)
            method_name = node.name
            method_color = method_colors[level]
            colored_method = deco.rgbstr(*method_color, method_name)
            colored_state = deco.yellow('cfn')
            print(f'{indent}    {colored_method} : {colored_state}')
    # now walk the global methods
    for node in ast.walk(the_ast):
      is_function = isinstance(node, ast.FunctionDef)
      if is_function:
        if node not in visited_functions:
          fn_name = node.name
          fn_color = function_colors[level]
          colored_method = deco.rgbstr(*fn_color, fn_name)
          colored_state = deco.yellow('gfn')
          print(f'{indent}  {colored_method} : {colored_state}')

         

###############################################################################

def iterate_package_contents(item_path : pathlib.Path, level: int):
  indent = '  ' * level
  short_name = item_path.parts[-1]
  pkgcolor = package_colors[level]
  colored_pkg = deco.rgbstr(*pkgcolor,short_name)
  colored_state = deco.yellow('package')
  print(f'{indent}{colored_pkg} : {colored_state}')
  # recursively enumerate the contents of the package
  for importer, modname, ispkg in pkgutil.iter_modules([str(item_path)]):
    if ispkg:
      iterate_package_contents(item_path / modname, level + 1)
    else:
      iterate_module_contents(item_path / modname, level + 1)

###############################################################################

def directory(ns_name : str):
  # enumerate all namespace packages in PYTHON_PATH with the given name "ns_name"
  # find all packages named "ns_name" in the PYTHON_PATH
  
  module_records_by_path = []
  
  # search for all namespace packages in PYTHON_PATH with the given name "ns_name"
  
  paths = sys.path
  for path in paths:
    as_p = pathlib.Path(path)
    ns_test = as_p / ns_name
    # check if the path has scripts as parent (via last part of path)
    if(len(as_p.parts)) > 0:
      has_scripts_as_parent = as_p.parts[-1] == 'scripts'
      if ns_test.exists() and has_scripts_as_parent:
        # check for namespace packages
        init_scr = ns_test / '__init__.py'
        if not init_scr.exists():
          # this is a namespace package
          print(f'Namespace package found: {ns_test}')
          module_records_by_path.append(ns_test)

  # now we have all namespace packages in PYTHON_PATH with the given name "ns_name"
  # we can enumerate the contents of each package (without importing it)
  # recursively enumerate the contents of each package
  # if a module has methods, enumerate them too
  for ns_path in module_records_by_path:
    colored_path = deco.path(ns_path)
    print(deco.val(f'Enumerating contents of namespace package: {colored_path}'))
    for importer, modname, ispkg in pkgutil.iter_modules([str(ns_path)]):
      if ispkg:
        iterate_package_contents(ns_path / modname, 0)
      else:
        iterate_module_contents(ns_path / modname, 0)


directory(args.ns_name)
