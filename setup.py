from setuptools import setup, find_packages
import glob, os
import platform

version = "0.0.154"

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
        dest_dir = os.path.join('obt', root)
        data_files.append((dest_dir, [filepath]))
  return data_files

###############################################################################

module_files = package_files('modules')
example_files = package_files('examples')
test_files = package_files('tests')
binpriv_files = package_files('bin_priv')
binpub_files = [f[1][0] for f in package_files("bin_pub")]

###############################################################################
data_files = module_files + example_files + test_files + binpriv_files
###############################################################################

setup(
    name="ork.build",
    version=version,
    author="Michael T. Mayers",
    author_email="michael@tweakoz.com",
    description="Orkid Build Tools",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="https://github.com/tweakoz/ork.build",
    packages=find_packages(where="scripts"),
    package_dir={
        "": "scripts",
    },
    data_files=data_files,
    scripts=binpub_files,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        'yarl',
        'toposort',
        'os-release',
        'distro',
        "twine",
        "build"
    ],
    )
