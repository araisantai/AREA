#!/usr/bin/env python3
"""Generate standalone AREA shell scripts from one template."""
from pathlib import Path

root = Path(__file__).resolve().parent.parent
template = (Path(__file__).resolve().parent / 'area.sh.tmpl').read_text(encoding='utf-8')
for filename, profile in (('linux_AREA.sh', 'linux'), ('AD_AREA.sh', 'ad')):
    path = root / filename
    path.write_text(template.replace('@PROFILE@', profile), encoding='utf-8')
    path.chmod(0o755)
    print(path)
