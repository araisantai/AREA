#!/usr/bin/env python3
"""Generate AREA shell launchers."""
from pathlib import Path
root = Path(__file__).resolve().parent.parent
for filename, profile in [('linux_AREA.sh', 'linux'), ('AD_AREA.sh', 'ad')]:
    path = root / filename
    path.write_text(f'''#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${{BASH_SOURCE[0]}}")" && pwd)"
exec python3 "$SCRIPT_DIR/builder/area.py" --profile {profile} "$@"
''', encoding='utf-8')
    path.chmod(0o755)
    print(path)
