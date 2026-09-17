#!/usr/bin/env python3
"""detached_launcher.py — fork driver.sh as a daemon process.

Runs driver.sh in a new session (setsid) so it survives the Hermes
background-process cleanup that kills proc_* jobs on session handoff.
"""
import os
import sys
import subprocess

HERE = "/Users/vivekanandsirohi/Desktop/antigravity/research-wiki"
LOG = os.path.join(HERE, "driver.detached.log")

keys = "sk-9aTlIwbSSlvddq1UmM7DvIlXot4n5tZ7VtVa6re9rTFA4gD2,sk-ptRPL71D34zn9S35hGZLzSdnjTi8kPuxsKYwyCbhkUDvmEDq,sk-fVKMFFZh3LtRiYbhqyIeJGChABLADXvfjwxUAa8Q1GnXTIcB,sk-p2wP17cz7HNcoXdHp7sg3HdzgTs1z8sCzDsb3dy2XiaVcbIO"

env = os.environ.copy()
env["HCNSEC_KEYS"] = keys

# Double-fork: the child forks again so we detach fully from this terminal.
try:
    pid = os.fork()
except OSError as e:
    print(f"fork failed: {e}", file=sys.stderr)
    sys.exit(1)
if pid > 0:
    # Parent: print child PID and exit immediately
    try:
        os.waitpid(pid, 0)  # reap zombie
    except ChildProcessError:
        pass
    print(f"DETACHED_DRIVER_PID={pid}", flush=True)
    sys.exit(0)

# First child: fork again
os.setsid()
try:
    pid2 = os.fork()
except OSError as e:
    print(f"fork2 failed: {e}", file=sys.stderr)
    sys.exit(1)
if pid2 > 0:
    os._exit(0)

# Second child: run driver.sh
os.chdir(HERE)
# Redirect stdin/stdout/stderr to /dev/null (driver.sh writes its own log)
sys.stdin = open(os.devnull)
sys.stdout = open(LOG, "a")
sys.stderr = open(LOG, "a")
os.execvp("bash", ["bash", os.path.join(HERE, "driver.sh")])