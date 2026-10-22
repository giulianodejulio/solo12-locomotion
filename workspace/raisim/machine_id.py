"""Read the genuine RaiSim machine ID from its unlicensed runtime diagnostic."""
import argparse
import json
from pathlib import Path
import re
import subprocess

CONTAINER = 'docker_solo12_raisim_ws'
PROBE = ('import sys; sys.path.insert(0,"/opt/raisimLib/raisim/linux/lib"); '
         'import raisimpy; world=raisimpy.World()')


def read_id():
    result = subprocess.run(['docker','exec',CONTAINER,'python3','-c',PROBE],
                            stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    match = re.search(r'Your machine id is:\s*([A-Fa-f0-9]{128})(?![A-Fa-f0-9])',result.stdout)
    if match is None:
        raise SystemExit('RaiSim did not report an unlicensed machine ID:\n'+result.stdout)
    return match.group(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-restart', action='store_true')
    args = parser.parse_args()
    machine_id = read_id()
    if args.verify_restart:
        subprocess.run(['docker','restart',CONTAINER],check=True,stdout=subprocess.PIPE)
        if read_id() != machine_id:
            raise SystemExit('Machine ID changed after restart; do not request a key yet')
    output = Path(__file__).resolve().parents[4]/'docker'/'raisim'
    output.mkdir(parents=True,exist_ok=True)
    path = output/'machine-id.txt'
    path.write_text(machine_id+'\n')
    path.chmod(0o600)
    (output/'identity-check.json').write_text(json.dumps(dict(
        container=CONTAINER,raisim_version='1.1.7',length=len(machine_id),
        stable_after_restart=args.verify_restart),indent=2)+'\n')
    print(machine_id)
    print(f'Length: {len(machine_id)}; restart verified: {args.verify_restart}')
    print(f'Saved privately outside Git: {path}')


if __name__=='__main__':
    main()
