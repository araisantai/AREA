import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'builder'))
import area

XML = '<nmaprun><host><address addr="192.0.2.10"/><ports><port protocol="tcp" portid="80"><state state="open"/><service name="http"/></port><port protocol="tcp" portid="22"><state state="open"/><service name="ssh"/></port></ports></host></nmaprun>'

class AreaTests(unittest.TestCase):
    def test_input_validation(self):
        self.assertEqual(area.target('EXAMPLE.com'), 'example.com')
        self.assertEqual(area.ports('443,80-81'), '80,81,443')
        for value in ['0.0.0.0/0', 'bad/target', '-invalid']:
            with self.assertRaises(Exception):
                area.target(value)

    def test_web_detection(self):
        self.assertEqual(area.web_urls(area.parse_nmap(XML)), ['http://192.0.2.10:80'])

    @patch('area.find_tool', side_effect=lambda name: name)
    @patch('area.command')
    def test_mocked_pipeline(self, run, _which):
        run.side_effect = [{'exit_code': 0, 'stdout': XML, 'stderr': ''}, {'exit_code': 0, 'stdout': '{"results":[]}', 'stderr': ''}]
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(area.main(['192.0.2.10', '--output', directory]), 0)
            result = json.loads((Path(directory) / 'results.json').read_text())
            self.assertEqual(result['web'][0]['url'], 'http://192.0.2.10:80')
            self.assertEqual(run.call_args_list[0].args[0][-2:], ['--', '192.0.2.10'])

if __name__ == '__main__':
    unittest.main()
