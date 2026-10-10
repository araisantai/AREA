import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GNMAP = 'Host: 192.0.2.10 (test.example)\tPorts: 22/open/tcp//ssh///, 80/open/tcp//http///, 443/closed/tcp//https///\n'


class GeneratedScriptTests(unittest.TestCase):
    def test_builder_generates_standalone_scripts(self):
        subprocess.run([str(ROOT / 'build.sh')], check=True, capture_output=True, text=True)
        template = (ROOT / 'builder/area.sh.tmpl').read_text()
        for name, profile in [('linux_AREA.sh', 'linux'), ('AD_AREA.sh', 'ad')]:
            script = ROOT / name
            self.assertEqual(script.read_text(), template.replace('@PROFILE@', profile))
            self.assertNotIn('python3', script.read_text())
            subprocess.run(['bash', '-n', str(script)], check=True)

    def test_copied_script_runs_elsewhere_and_writes_to_cwd(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            script = work / 'linux_AREA.sh'
            shutil.copy2(ROOT / 'linux_AREA.sh', script)
            bindir = work / 'bin'
            bindir.mkdir()
            nmap = bindir / 'nmap'
            nmap.write_text('''#!/usr/bin/env bash
set -euo pipefail
xml=''; gnmap=''
while (( $# )); do
  case "$1" in
    -oX) xml="$2"; shift 2 ;;
    -oG) gnmap="$2"; shift 2 ;;
    *) shift ;;
  esac
done
printf '<nmaprun/>\\n' > "$xml"
printf 'Host: 192.0.2.10 (test.example)\\tPorts: 22/open/tcp//ssh///, 80/open/tcp//http///, 443/closed/tcp//https///\\n' > "$gnmap"
''')
            nmap.chmod(0o755)
            ferox = bindir / 'feroxbuster'
            ferox.write_text('#!/usr/bin/env bash\nprintf \'{"url":"%s"}\\n\' "$2"\n')
            ferox.chmod(0o755)
            env = dict(os.environ, PATH=str(bindir) + os.pathsep + os.environ['PATH'])
            result = subprocess.run([str(script), '192.0.2.10', '--web-tools', 'feroxbuster'], cwd=work, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            runs = list((work / 'AREA_output').iterdir())
            self.assertEqual(len(runs), 1)
            self.assertEqual((runs[0] / 'web_urls.txt').read_text(), 'http://192.0.2.10:80\n')
            self.assertTrue((runs[0] / 'tcp.xml').exists())
            self.assertTrue((runs[0] / 'web/feroxbuster_1.jsonl').exists())

    def test_invalid_target_does_not_create_output(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([str(ROOT / 'linux_AREA.sh'), 'bad;target'], cwd=directory, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((Path(directory) / 'AREA_output').exists())


if __name__ == '__main__':
    unittest.main()
