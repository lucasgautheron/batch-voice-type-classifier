import subprocess
import argparse
import os
import shutil
import sys


parser = argparse.ArgumentParser()
parser.add_argument("--inputs", nargs="+", default=[])
parser.add_argument("--destinations", nargs="+", default=[])
parser.add_argument("--tmpnames", nargs="+", default=[])
args = parser.parse_args()

inputs = list(map(os.path.abspath, args.inputs))
destinations = list(map(os.path.abspath, args.destinations))
tmpnames = args.tmpnames

if len(inputs) != len(destinations) or len(inputs) != len(tmpnames):
    print('wrong input')
    sys.exit(1)

for i in range(len(inputs)):
    input = inputs[i]
    destination = destinations[i]
    tmpname = tmpnames[i]

    os.symlink(input, os.path.join('tmp', tmpname))
    subprocess.call(['./apply.sh', os.path.join('tmp', tmpname), '--device=gpu', '--batch=8'])
    shutil.copy(os.path.join('voice-type-classifier/output', os.path.basename(tmpname), 'all.rttm'), destination)

print('complete')