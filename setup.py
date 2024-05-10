from setuptools import setup, find_packages, Command
from setuptools.command.install import install
import os
import stat

version = "0.0.177"

# Read the long description from the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

def package_files(directory):
    data_files = []
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if not (filename.endswith('.pyc') or '.egg-info' in root or '__pycache__' in root):
                filepath = os.path.join(root, filename)
                dest_dir = os.path.join('obt', root)
                data_files.append((dest_dir, [filepath]))
    return data_files

example_files = package_files('examples')
test_files = package_files('tests')
binpub_files = [f[1][0] for f in package_files("bin_pub")]
binpriv_files = package_files('bin_priv')
data_files = example_files + test_files + binpriv_files

class PostInstallCommand(install):
    """Post-installation for setting permissions on specific directories."""
    def run(self):
        install.run(self)
        # Set permissions for the directories
        directories = ['scripts/obt/bin_priv', 'scripts/obt/obt_modules']
        for directory in directories:
            full_path = os.path.join(self.install_lib, 'ork.build', directory)
            for root, dirs, files in os.walk(full_path):
                for file in files:
                    os.chmod(os.path.join(root, file), stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)

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
    package_dir={"": "scripts"},
    include_package_data=True,
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
        "build",
        "conan"
    ],
    cmdclass={
        'install': PostInstallCommand,
    }
)
