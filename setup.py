from setuptools import setup, find_packages
import glob, os
import platform

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
                if platform.system() == 'Darwin':  # This means it's macOS
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
      if platform.system() == 'Linux':
          sysmatch = 'obt.osx' not in f
      if platform.system() == 'Darwin':
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

setup(
    name="ork.build.tools",
    version="0.0.10",
    packages=find_packages(exclude=["bin_priv", "build", "dist"]),
    package_dir={
        "": ".",
    },
    data_files=module_files + example_files + test_files + binpriv_files,
    scripts=glob_platform_specific('bin_pub/*'),
    long_description=long_description,
    long_description_content_type='text/markdown'
)
