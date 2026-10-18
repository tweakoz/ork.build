"""Small, side-effect-free checks for installed dependency versions."""
import re
import subprocess
from pathlib import Path


def defines_version(filename, prefix, version, suffix=""):
    try:
        text = Path(filename).read_text()
    except (OSError, UnicodeError):
        return False
    for name, number in zip(('MAJOR', 'MINOR', 'PATCH', 'TWEAK'), version.split('.')):
        match = re.search(r'^\s*#\s*define\s+' + re.escape(prefix + name + suffix) +
                          r'\s+(\d+)\b', text, re.MULTILINE)
        if not match or int(match.group(1)) != int(number):
            return False
    return True


def cmake_version(filename, version):
    try:
        text = Path(filename).read_text()
    except (OSError, UnicodeError):
        return False
    return bool(re.search(r'\bset\s*\(\s*PACKAGE_VERSION\s+"' +
                          re.escape(version) + r'"\s*\)', text, re.IGNORECASE))


def command_version(argv, version):
    try:
        text = subprocess.check_output([str(arg) for arg in argv], text=True,
                                       stderr=subprocess.STDOUT, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return False
    return bool(re.search(r'(?<![\d.])' + re.escape(version) + r'(?![\d.])', text))


def python_extension_suffix(executable):
    # Ask the target interpreter, not OBT's potentially different host Python.
    suffix = subprocess.check_output([str(executable), '-I', '-c',
        'import sysconfig; print(sysconfig.get_config_var("EXT_SUFFIX") or "")'],
        text=True, stderr=subprocess.STDOUT, timeout=10).strip()
    if not suffix.startswith('.') or '/' in suffix or '\\' in suffix or '\n' in suffix:
        raise RuntimeError('Target Python did not return a valid extension suffix')
    return suffix
