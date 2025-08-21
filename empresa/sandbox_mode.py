"""
Small in-process sandbox-mode helper used to silence external side-effects
during simulation runs.

This is intentionally minimal: it provides module-level enable/disable
functions and a query function. The SimulacionService enables the sandbox
while running business side-effects in a DB savepoint. Other modules (email,
http callers, task enqueuers) should check is_sandbox() before performing
external I/O.
"""
_SANDBOX = False

def enable():
    global _SANDBOX
    _SANDBOX = True

def disable():
    global _SANDBOX
    _SANDBOX = False

def is_sandbox():
    return bool(_SANDBOX)
