# AREA

AREA V1 is a Python reconnaissance runner for authorized scope. The Python source and generator live in `builder/`; all checks live in `test/`.

```bash
./build.sh
./installer-setup.sh --check
./installer-setup.sh
python3 -m unittest discover -s test -v
```

`build.sh` regenerates `linux_AREA.sh` and `AD_AREA.sh`. The installer reports the detected version of each existing tool, then installs only missing tools. `--check` reports versions and missing tools without installing; it exits nonzero if something is missing. On macOS, Nmap and feroxbuster use Homebrew. On Linux, they use apt. Dirsearch is installed from its official GitHub source into a project-local `.tools/` virtual environment, so Python 3.11+ and git are required. The runner finds that local dirsearch automatically.

Requires Python 3.11+, Nmap, and optionally feroxbuster, dirsearch, or ffuf.

```bash
./linux_AREA.sh 192.0.2.10 --mode all --ports 22,80,443 --scripts --output out/linux
./linux_AREA.sh example.com --mode web-enum --web-tools feroxbuster ffuf --wordlist /path/to/words.txt
./AD_AREA.sh 192.0.2.0/28 --udp --output out/ad
```

Results are written to `results.json` with normalized open ports, web URLs, command output, and errors. The raw scan is saved as `nmap.xml`. The AD profile selects common AD TCP ports by default. `--ports` overrides either profile, `--udp` adds a small UDP scan, and `--scripts` enables Nmap default scripts. Web discovery runs only for detected HTTP services.

## Next development

1. Normalize and deduplicate web discoveries; filter wildcard and soft-404 responses.
2. Add resumable jobs, per-host rate limits, explicit scope files, and exclusions.
3. Add read-only SMB, LDAP, and RPC modules triggered by detected ports.
4. Version the output schema and capture evidence paths for downstream AI analysis.
5. Add `users.txt` and `pass.txt` handling with explicit credential-testing authorization and lockout safeguards. Keep a future `spray` mode separate from enumeration.
