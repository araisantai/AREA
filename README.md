# AREA

AREA V1 builds standalone Bash reconnaissance scripts for authorized scope. Python is needed only to generate the scripts; the generated files run without Python or other AREA project files. The source template and generator live in `builder/`; checks live in `test/`.

```bash
./build.sh
./installer-setup.sh --check
./installer-setup.sh
python3 -m unittest discover -s test -v
```

`build.sh` regenerates `linux_AREA.sh` and `AD_AREA.sh`. Copy either generated script to another directory or machine that has its tools installed. The installer reports the detected version of each existing tool, then installs only missing tools. `--check` reports versions and missing tools without installing; it exits nonzero if something is missing. On macOS, Nmap and feroxbuster use Homebrew. On Linux, they use apt. Dirsearch uses pipx and its official GitHub source, so Python 3.11+ and git are required. Generated scripts find tools on PATH or in `~/.local/bin`.

Generated scripts require Bash, Nmap, awk, sort, and optionally feroxbuster, dirsearch, or ffuf. Python 3.11+ is needed only to build scripts and install dirsearch.

```bash
./linux_AREA.sh 192.0.2.10 --mode all --ports 22,80,443 --scripts
./linux_AREA.sh example.com --mode web-enum --web-tools feroxbuster,ffuf --wordlist /path/to/words.txt
./AD_AREA.sh 192.0.2.0/28 --udp
```

Each run creates `./AREA_output/<profile>_<timestamp>_<pid>/` under the directory where you launch the script. It contains `manifest.tsv`, Nmap XML and grepable output, `web_urls.txt`, logs, and per-tool results under `web/`. The AD profile selects common AD TCP ports by default. `--ports` overrides either profile, `--udp` adds a separate small UDP scan, and `--scripts` enables Nmap default scripts. Web discovery runs only for detected HTTP services.

## Next development

1. Normalize and deduplicate web discoveries; filter wildcard and soft-404 responses.
2. Add resumable jobs, per-host rate limits, explicit scope files, and exclusions.
3. Add read-only SMB, LDAP, and RPC modules triggered by detected ports.
4. Version the output schema and capture evidence paths for downstream AI analysis.
5. Add `users.txt` and `pass.txt` handling with explicit credential-testing authorization and lockout safeguards. Keep a future `spray` mode separate from enumeration.



The command to updates next i will only need to saya
update the builder to do this things
- x
- x
- x
auto build again the sh scripts. and make the test checker, also if there is new prequisites please updates it. after push all updated changes to my repo