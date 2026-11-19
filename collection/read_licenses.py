import json
import sys
import subprocess
import uuid
from helpcat.collect import bounded_run, build_command, atomic_write

image = sys.argv[1]
script = r"""
import importlib.metadata as md,json,hashlib
packages=['black','pipx','pipenv','tox','virtualenv','httpie','rich-cli','sqlfluff','hatch','datasette']
result=[]
for package in packages:
 d=md.distribution(package)
 notices=[]
 for p in d.files or []:
  name=str(p)
  if '.dist-info/' in name and any(x in name.lower() for x in ['license','copying','notice']):
   raw=d.locate_file(p).read_bytes()
   notices.append({'path':name,'text':raw.decode('utf-8',errors='strict'),'sha256':hashlib.sha256(raw).hexdigest()})
 result.append({'package':package,'version':d.version,'notices':notices})
print(json.dumps(result))
"""
name = "helpcat-notices-" + uuid.uuid4().hex
try:
    result = bounded_run(
        build_command("podman", image, ["python", "-c", script], name=name),
        timeout=20,
        max_bytes=1048576,
    )
finally:
    subprocess.run(
        ["podman", "rm", "--force", name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        timeout=10,
    )
if result["status"] != "ok":
    raise SystemExit(result["stderr"].decode())
notices = json.loads(result["stdout"])
output = sys.argv[2] if len(sys.argv) > 2 else "/tmp/helpcat-licenses.json"
atomic_write(output, (json.dumps(notices, indent=2) + "\n").encode())
print([(r["package"], len(r["notices"])) for r in notices])
