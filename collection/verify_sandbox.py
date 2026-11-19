"""Run this script inside the same collection container."""

import json
import os
from pathlib import Path
import socket
import tempfile

mounts = [line.split() for line in Path("/proc/mounts").read_text().splitlines()]
root_options = next(fields[3].split(",") for fields in mounts if fields[1] == "/")
with tempfile.TemporaryFile(dir="/tmp") as stream:
    stream.write(b"probe")
    temporary_storage = True
checks = {
    "uid": os.getuid(),
    "root_read_only": "ro" in root_options,
    "temporary_storage": temporary_storage,
    "network_interfaces": [name for _, name in socket.if_nameindex()],
    "memory_max": Path("/sys/fs/cgroup/memory.max").read_text().strip(),
    "cpu_max": Path("/sys/fs/cgroup/cpu.max").read_text().strip(),
    "pids_max": Path("/sys/fs/cgroup/pids.max").read_text().strip(),
}
assert checks["uid"] == 65534
assert checks["root_read_only"]
assert checks["network_interfaces"] == ["lo"]
assert checks["memory_max"] == "536870912"
assert checks["pids_max"] == "64"
quota, period = map(int, checks["cpu_max"].split())
assert quota / period == 1
print(json.dumps(checks, indent=2))
