from setuptools import setup, find_packages
import glob

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='ork.build.tools',
    packages=find_packages(where='scripts'),
    package_dir={'': 'scripts'},
    scripts=glob.glob('bin_pub/*'),
    long_description=long_description,
    long_description_content_type='text/markdown')
