###############################################################################
# Orkid Build Tools
# Retry helper for transient subprocess failures (wget, git, pip).
#
# All functions assume an integer rc convention: 0 == success, non-zero == fail.
###############################################################################

import time


DEFAULT_ATTEMPTS = 3
DEFAULT_BACKOFF  = (2, 6)   # seconds before retry #1 and retry #2


def retry_until_rc_zero(invoke,
                        attempts=DEFAULT_ATTEMPTS,
                        backoff=DEFAULT_BACKOFF,
                        label="op",
                        cleanup=None):
  """Repeatedly call invoke() until it returns 0.

  invoke   : zero-arg callable returning an integer return code.
  attempts : total number of tries (1 + retries).
  backoff  : tuple of seconds to wait BEFORE retry #i (i in 1..attempts-1).
             clamped to the last element if i exceeds the tuple length.
  label    : human-readable label for log lines.
  cleanup  : optional zero-arg callable run BEFORE each retry (not the
             first attempt). Use this to wipe partial state (e.g. a half-
             cloned git repo) so the retry starts clean.

  Returns 0 on first success, or the last non-zero rc on terminal failure.
  Exceptions raised by invoke() are caught and treated as rc=-1 so the
  retry loop can continue.
  """
  rc = -1
  for i in range(attempts):
    if i > 0:
      wait = backoff[min(i - 1, len(backoff) - 1)]
      print("  retry %d/%d: %s (sleeping %ds)" % (i, attempts - 1, label, wait))
      time.sleep(wait)
      if cleanup is not None:
        try:
          cleanup()
        except Exception as e:
          print("  cleanup before retry %d raised %s: %s" %
                (i, type(e).__name__, e))
    try:
      rc = invoke()
    except Exception as e:
      print("  attempt %d/%d: %s raised %s: %s" %
            (i + 1, attempts, label, type(e).__name__, e))
      rc = -1
      continue
    if rc == 0:
      return 0
  return rc
