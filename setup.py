from setuptools import setup, find_packages
import glob

setup(
    packages=find_packages(where='scripts'),
    package_dir={'': 'scripts'},
    scripts=glob.glob('bin_pub/*'),
)
