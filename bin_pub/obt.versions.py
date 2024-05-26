#!/usr/bin/env python3 

import os
import sys
import site
import obt.path
import importlib.metadata

def print_env_var(name, default):
    value = os.getenv(name, default)
    print(f"{name}: {value}")

print( "######################################################")

print_env_var('PYTHONPATH', sys.path)
print_env_var('PYTHONHOME', sys.prefix)
print_env_var('PYTHONSTARTUP', 'Not set')
print_env_var('PYTHONUSERBASE', site.USER_BASE)
print_env_var('PYTHONEXECUTABLE', sys.executable)
print_env_var('PYTHONWARNINGS', 'Not set')
print_env_var('PYTHONNOUSERSITE', 'Not set (User site directory is added to sys.path)')
print_env_var('PYTHONUNBUFFERED', 'Not set (Buffered I/O is used for stdout and stderr)')

print_env_var('site.PREFIXES', site.PREFIXES)
print_env_var('site.USER_SITE', site.USER_SITE)
print_env_var('site.USER_BASE', site.USER_BASE)
print_env_var('sys.prefix', sys.prefix)
print_env_var('sys.base_prefix', sys.base_prefix)

print( "######################################################")

a = importlib.metadata.distribution("ork.build").metadata

print( "obt-pymodule-path: %s" % obt.path.obt_module_path() )
print( "obt-data-base: %s" % obt.path.obt_data_base() )
print( "obt-modules-test: %s" % obt.path.__get_modules() )
print( "obt-test-inplace: %s" % obt.path.__is_inplace() )
print( "obt-modules-base: %s" % obt.path.obt_modules_base() )
print( "running_from_pip: %s" % obt.path.running_from_pip() )
print( "running_in_tree: %s" % obt.path.obt_in_tree() )
print( "obt.distrib.name: %s" % a["Name"] )
print( "obt.distrib.version: %s" % a["Version"] )
print( "obt.distrib.author: %s" % a["Author"] )
print( "obt.distrib.author-email: %s" % a["Author-email"] )
print( "obt.distrib.summary: %s" % a["Summary"] )
print( "obt.distrib.homepage: %s" % a["Home-page"] )
