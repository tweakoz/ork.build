from setuptools import setup, find_packages
import glob, os

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

def package_files(directory):
    data_files = []
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if not (filename.endswith('.pyc') or '.egg-info' in root or '__pycache__' in root):
                filepath = os.path.join(root, filename)
                data_files.append((os.path.join('ork.build.tools', root), [filepath]))
    return data_files

module_files = package_files('modules')
example_files = package_files('examples')
test_files = package_files('tests')

data_files = module_files + example_files + test_files

setup(
    name="ork.build.tools",
    version="0.0.6",
    packages=find_packages(),
    package_dir={
        "": ".",
    },
    data_files=data_files,
    scripts=glob.glob('bin_pub/*'),
    long_description=long_description,
    long_description_content_type='text/markdown'
)