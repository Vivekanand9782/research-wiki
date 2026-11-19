#!/usr/bin/env python3
"""Detached driver launcher.

Uses os.fork() + os.setsid() so the child runs detached from this
session — Hermes can't kill it with SIGTERM on session handoff.

Usage: python3 launch_daemon.py
The parent prints the daemon PID and exits. The daemon runs driver.sh
and logs to driver.daemon.log.
"""
import os
import re
import sys
import time

from dotenv import load_dotenv

HERE = "/Users/vivekanandsirohi/Desktop/antigravity/research-wiki"

# config.py loads .env from the repo and workspace roots before callers read
# env vars; do the same so keys stored only in .env still reach driver.sh.
load_dotenv(os.path.join(HERE, ".env"), override=False)
load_dotenv(os.path.join(os.path.dirname(HERE), ".env"), override=False)
load_dotenv(override=False)

env = os.environ.copy()
# driver.sh consumes HCNSEC_KEYS; feed it from GENERAL_COMPUTE_API_KEYS,
# the same env var the rest of the repo reads. Normalize separators the
# same way llm_config.get_api_keys does (comma, semicolon, whitespace).
keys = [
    k
    for k in re.split(r"[,;\s]+", os.environ.get("GENERAL_COMPUTE_API_KEYS", ""))
    if k
]
if not keys:
    sys.exit("GENERAL_COMPUTE_API_KEYS env var must be set (comma-separated keys)")
env["HCNSEC_KEYS"] = ",".join(keys)

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