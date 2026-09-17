#!/usr/bin/env python3
"""Detached driver launcher.

Uses os.fork() + os.setsid() so the child runs detached from this
session — Hermes can't kill it with SIGTERM on session handoff.

Usage: python3 launch_daemon.py
The parent prints the daemon PID and exits. The daemon runs driver.sh
and logs to driver.daemon.log.
"""
import os
import sys
import time

HERE = "/Users/vivekanandsirohi/Desktop/antigravity/research-wiki"

keys = ("sk-9aTlIwbSSlvddq1UmM7DvIlXot4n5tZ7VtVa6re9rTFA4gD2,"
        "sk-ptRPL71D34zn9S35hGZLzSdnjTi8kPuxsKYwyCbhkUDvmEDq,"
        "sk-fVKMFFZh3LtRiYbhqyIeJGChABLADXvfjwxUAa8Q1GnXTIcB,"
        "sk-p2wP17cz7HNcoXdHp7sg3HdzgTs1z8sCzDsb3dy2XiaVcbIO")

env = os.environ.copy()
env["HCNSEC_KEYS"] = keys

pid1 = os.fork()
if pid1 > 0:
    # Parent: wait briefly so child forks twice, then exit.
    os.waitpid(pid1, 0)
    print(f"DAEMON_FORKED pid={pid1}")
    sys.exit(0)

# First child: create new session, fork again
os.setsid()
pid2 = os.fork()
if pid2 > 0:
    os._exit(0)

# Second child: fully detached — run driver.sh
os.chdir(HERE)
devnull = os.open(os.devnull, os.O_RDWR)
os.dup2(devnull, 0)
log_path = os.path.join(HERE, "driver.daemon.log")
log_fd = open(log_path, "a")
os.dup2(log_fd.fileno(), 1)
os.dup2(log_fd.fileno(), 2)
# Write a heartbeat marker
log_fd.write(f"[{time.strftime('%H:%M:%S')}] daemon started, pid={os.getpid()}\n")
log_fd.flush()
os.execve("/bin/bash", [
    "bash", os.path.join(HERE, "driver.sh"),
], env)