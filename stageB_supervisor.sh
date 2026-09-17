#!/usr/bin/env bash
# Waits for the Stage A render (pid $1) to finish, then launches the
# detached deep-summary daemon (driver.sh) for the remaining pending papers.
cd "$(dirname "$0")"
PID="${1:?usage: stageB_supervisor.sh <render_pid>}"
echo "[$(date +'%F %T')] supervisor waiting for render pid $PID" >> stageB_supervisor.log
while ps -p "$PID" > /dev/null 2>&1; do sleep 30; done
echo "[$(date +'%F %T')] Stage A render finished; launching daemon" >> stageB_supervisor.log
python3 launch_daemon.py >> stageB_supervisor.log 2>&1
echo "[$(date +'%F %T')] daemon launch done" >> stageB_supervisor.log
