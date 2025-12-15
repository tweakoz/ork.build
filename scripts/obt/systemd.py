#!/usr/bin/env python3
"""
OBT Systemd Module
Provides module discovery and loading for systemd user services.
Pattern follows obt.dep and obt.docker modules.
"""

import os
import sys
import importlib.util
from pathlib import Path

def enumerate():
    """
    Returns list of all available service module names.
    Scans $OBT_MODULES_PATH/systemd/ directories for *.py files.
    """
    services = set()
    module_paths = os.environ.get("OBT_MODULES_PATH", "").split(":")

    for base_path in module_paths:
        if not base_path:
            continue
        systemd_dir = Path(base_path) / "systemd"
        if systemd_dir.exists() and systemd_dir.is_dir():
            for py_file in systemd_dir.glob("*.py"):
                if py_file.stem != "__init__":
                    services.add(py_file.stem)

    return sorted(services)

def requires(service_name):
    """
    Load and return serviceinfo instance for given service name.
    Searches $OBT_MODULES_PATH in order, returns first match.

    Args:
        service_name: Name of the service module (e.g., "ork_logger_http")

    Returns:
        serviceinfo instance from the loaded module

    Raises:
        RuntimeError: If service module not found
    """
    module_paths = os.environ.get("OBT_MODULES_PATH", "").split(":")

    for base_path in module_paths:
        if not base_path:
            continue
        systemd_dir = Path(base_path) / "systemd"
        module_file = systemd_dir / f"{service_name}.py"

        if module_file.exists():
            # Load the module dynamically
            spec = importlib.util.spec_from_file_location(
                f"obt.modules.systemd.{service_name}",
                module_file
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module
                spec.loader.exec_module(module)

                # Instantiate and return serviceinfo
                if hasattr(module, 'serviceinfo'):
                    return module.serviceinfo()
                else:
                    raise RuntimeError(
                        f"Service module '{service_name}' does not have 'serviceinfo' class"
                    )

    raise RuntimeError(f"Service module '{service_name}' not found in OBT_MODULES_PATH")
