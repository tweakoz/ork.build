from setuptools import setup, find_packages
import glob, os
import platform

assert("OBT_DEPLOY_TARGET" in os.environ)
sel_platform = os.environ["OBT_DEPLOY_TARGET"]
assert( sel_platform in ["linux","macos"])

###############################################################################

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

###############################################################################

def package_files(directory):
    data_files = []
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if not (filename.endswith('.pyc') or '.egg-info' in root or '__pycache__' in root):
                filepath = os.path.join(root, filename)
                data_files.append((os.path.join('ork.build.tools', root), [filepath]))
    return data_files

###############################################################################

def package_files_platform_specific(directory):
    data_files = []
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if not (filename.endswith('.pyc') or '.egg-info' in root or '__pycache__' in root):
                filepath = os.path.join(root, filename)
                if sel_platform == 'macos':  # This means it's macOS
                    if "obt.ix" in filepath:
                        continue
                else:  # For any other OS, we skip 'obt.osx'
                    if "obt.osx" in filepath:
                        continue
                data_files.append((os.path.join('ork.build.tools', root), [filepath]))
    return data_files

###############################################################################

def glob_platform_specific(directory):
    files = glob.glob(directory)
    outfiles = []
    for f in files:
      if sel_platform == 'linux':
          sysmatch = 'obt.osx' not in f
      if sel_platform == 'macos':
          sysmatch = 'obt.ix' not in f
      if sysmatch:
        outfiles.append(f)
    return outfiles

###############################################################################

module_files = package_files('modules')
example_files = package_files('examples')
test_files = package_files('tests')
binpriv_files = package_files_platform_specific('bin_priv')

###############################################################################


###############################################################################

setup(
    name="ork.build.tools",
    version="0.0.12",
    packages=find_packages(exclude=["bin_priv", "build", "dist"]),
    package_dir={
        "": ".",
    },
    data_files=module_files + example_files + test_files + binpriv_files,
    scripts=glob_platform_specific('bin_pub/*'),
    long_description=long_description,
    long_description_content_type='text/markdown'
)
