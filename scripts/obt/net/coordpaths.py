"""obt.net.coordpaths — the ONE root for coordination identity + mail paths.

Every coordination path hangs off coord_home(): the seat identity/config
(`.obt-global/obtnet.json`) and the mail tree (`coordination/` — inbox,
inbox.stream, acked, bin, tasksets, ...).

  OBT_COORD_HOME unset  -> Path.home(), byte-identical to the behavior that
                           existed before this override.
  OBT_COORD_HOME set    -> that directory replaces the home root, so a second
                           coordinator seat can share a login account without
                           sharing an identity, a controller address, or an
                           inbox with the first one.

Paths are computed PER CALL (never captured in module-level constants) so an
in-process env change relocates them — the property the seat tool already
relied on, now spelled once for everybody.

Two bin tools carry a hand-mirror of coord_home() by necessity, NOT by
oversight: obt.net.msg.deposit.py is copied to remote seats and runs under
bare system python3 (the `obt` package is not importable there), and
obt.coord.seat.py must work before obt is installed. Their mirrors are three
lines with identical semantics — one env read, home fallback. Change them
together.
"""

import os
from pathlib import Path

ENV_VAR = "OBT_COORD_HOME"


def coord_home() -> Path:
    """Root for coordination identity + mail. $OBT_COORD_HOME, else $HOME.
    An empty value counts as unset (a blank export must not silently point
    coordination at the filesystem root)."""
    val = os.environ.get(ENV_VAR)
    return Path(val).expanduser() if val else Path.home()


def config_path() -> Path:
    """The seat identity/config file: <coord_home>/.obt-global/obtnet.json."""
    return coord_home() / ".obt-global" / "obtnet.json"


def coord_root() -> Path:
    """The seat mail/taskset tree: <coord_home>/coordination."""
    return coord_home() / "coordination"
