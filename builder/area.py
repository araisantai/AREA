#!/usr/bin/env python3
"""AREA V1 scoped reconnaissance runner."""
import argparse
import ipaddress
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def find_tool(name):
    local = PROJECT_ROOT / '.tools' / 'bin' / name
    if local.is_file():
        return str(local)
    return shutil.which(name)

WEB_PORTS = {80, 81, 443, 8000, 8008, 8080, 8081, 8443, 8888}

def target(value):
    try:
        net = ipaddress.ip_network(value, strict=False)
        if net.num_addresses > 4096:
            raise argparse.ArgumentTypeError('CIDR exceeds 4096 addresses')
        return str(net) if '/' in value else str(net.network_address)
    except ValueError:
        pass
    if '/' in value or '..' in value or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.-]{0,251}[A-Za-z0-9]', value):
        raise argparse.ArgumentTypeError('expected IP, CIDR, or DNS name')
    return value.lower()

def ports(value):
    selected = set()
    try:
        for part in value.split(','):
            if '-' in part:
                first, last = map(int, part.split('-'))
                if first > last:
                    raise ValueError()
                selected.update(range(first, last + 1))
            else:
                selected.add(int(part))
        if not selected or min(selected) < 1 or max(selected) > 65535:
            raise ValueError()
    except ValueError:
        raise argparse.ArgumentTypeError('expected ports 1-65535') from None
    return ','.join(map(str, sorted(selected)))

def command(argv, timeout):
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
        return {'exit_code': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {'exit_code': None, 'stdout': '', 'stderr': str(exc)}

def parse_nmap(xml):
    hosts = []
    for node in ET.fromstring(xml).findall('host'):
        address = node.find('address')
        if address is None:
            continue
        host = {'address': address.get('addr'), 'ports': []}
        for port in node.findall('./ports/port'):
            state = port.find('state')
            if state is None or state.get('state') != 'open':
                continue
            service = port.find('service')
            host['ports'].append({'protocol': port.get('protocol'), 'port': int(port.get('portid')), 'service': service.attrib if service is not None else {}, 'scripts': [s.attrib for s in port.findall('script')]})
        hosts.append(host)
    return hosts

def web_urls(hosts):
    found = set()
    for host in hosts:
        for port in host['ports']:
            number = port['port']
            name = port['service'].get('name', '').lower()
            if port['protocol'] != 'tcp' or (number not in WEB_PORTS and 'http' not in name):
                continue
            scheme = 'https' if number in {443, 8443} or 'https' in name or 'ssl' in name else 'http'
            address = host['address']
            if ':' in address:
                address = f'[{address}]'
            found.add(f'{scheme}://{address}:{number}')
    return sorted(found)

def execute(args):
    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    result = {'schema_version': 1, 'started_at': datetime.now(timezone.utc).isoformat(), 'target': args.target, 'mode': args.mode, 'profile': args.profile, 'hosts': [], 'web': [], 'errors': []}
    nmap = find_tool('nmap')
    if not nmap:
        result['errors'].append('nmap is not installed')
    else:
        scan = [nmap, '-Pn', '-sT', '-sV', '-oX', '-']
        if args.ports:
            scan += ['-p', args.ports]
        elif args.profile == 'ad':
            scan += ['-p', '53,88,135,139,389,445,464,636,3268,3269,3389,5985,5986']
        else:
            scan += ['--top-ports', '1000']
        if args.udp:
            scan += ['-sU', '--top-ports', str(args.udp_ports)]
        if args.scripts:
            scan += ['-sC']
        scan += ['--', args.target]
        run = command(scan, args.timeout)
        (out / 'nmap.xml').write_text(run['stdout'], encoding='utf-8')
        if run['exit_code'] != 0:
            result['errors'].append(f"nmap failed: {run['stderr'].strip()}")
        try:
            result['hosts'] = parse_nmap(run['stdout'])
        except ET.ParseError as exc:
            result['errors'].append(f'invalid nmap XML: {exc}')
    for index, url in enumerate(web_urls(result['hosts'])):
        item = {'url': url, 'discoveries': {}, 'errors': []}
        for tool in args.web_tools:
            executable = find_tool(tool)
            if not executable:
                item['errors'].append(f'{tool} is not installed')
                continue
            if tool == 'feroxbuster':
                cmd = [executable, '--url', url, '--json', '--silent', '--stdout']
            elif tool == 'dirsearch':
                cmd = [executable, '-u', url, '--format', 'json', '--output', str(out / f'dirsearch-{index}.json')]
            else:
                if not args.wordlist:
                    item['errors'].append('ffuf requires --wordlist')
                    continue
                cmd = [executable, '-u', url + '/FUZZ', '-w', args.wordlist, '-of', 'json', '-o', str(out / f'ffuf-{index}.json')]
            item['discoveries'][tool] = command(cmd, args.timeout)
        result['web'].append(item)
    result['finished_at'] = datetime.now(timezone.utc).isoformat()
    (out / 'results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return 1 if result['errors'] else 0

def main(argv=None):
    parser = argparse.ArgumentParser(description='AREA V1 (authorized targets only)')
    parser.add_argument('target', type=target)
    parser.add_argument('--mode', choices=['all', 'web-enum'], default='all')
    parser.add_argument('--profile', choices=['linux', 'ad'], default='linux')
    parser.add_argument('--ports', type=ports)
    parser.add_argument('--udp', action='store_true')
    parser.add_argument('--udp-ports', type=int, choices=range(1, 101), metavar='1-100', default=20)
    parser.add_argument('--scripts', action='store_true')
    parser.add_argument('--web-tools', nargs='*', choices=['dirsearch', 'feroxbuster', 'ffuf'], default=['feroxbuster'])
    parser.add_argument('--wordlist')
    parser.add_argument('--timeout', type=int, default=1800)
    parser.add_argument('--output', default='area-output')
    args = parser.parse_args(argv)
    if args.timeout < 1:
        parser.error('--timeout must be positive')
    return execute(args)

if __name__ == '__main__':
    sys.exit(main())
