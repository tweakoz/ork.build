###############################################################################
# Orkid Build System
# Copyright 2010-2025, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

class serviceinfo:
    """
    Systemd service module for Orkid HTTP Logger Server.
    Provides metadata and configuration for the ork.logger.httpserver service.
    """
    def __init__(self):
        self._name = "ork_logger_http"
        self._command = "ork.logger.httpserver.py"
        self._description = "Orkid HTTP Logger Service - Receives and displays log messages from Orkid applications"
        self._requires = []  # Hard dependencies (fails if dependency fails)
        self._prefers = []   # Soft dependencies (doesn't fail if missing)
        self._after = []     # Start after these (ordering only)
        self._before = []    # Start before these (ordering only)
        self._requires_deps = []     # OBT dep modules to realize (e.g., ["lua", "vulkan"])
        self._requires_dockers = []  # Docker modules to build (e.g., ["postgres_dev"])
        self._requires_pips = []     # Python packages to pip install (e.g., ["flask", "redis"])
        self._requires_tty = None    # TTY number for graphical daemons (e.g., 7 for /dev/tty7)
        self._as_system_service = False  # Run as system service (requires sudo to install)

    def info(self):
        """
        Return service metadata dictionary.
        """
        return {
            "name": self._name,
            "command": self._command,
            "description": self._description,
            "requires": self._requires,
            "prefers": self._prefers,
            "after": self._after,
            "before": self._before,
            "requires_deps": self._requires_deps,
            "requires_dockers": self._requires_dockers,
            "requires_pips": self._requires_pips,
            "requires_tty": self._requires_tty,
            "as_system_service": self._as_system_service,
        }
