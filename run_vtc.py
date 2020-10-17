import subprocess
import argparse
import os
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--inputs", nargs="+", default=[])
parser.add_argument("--destinations", nargs="+", default=[])
args = parser.parse_args()

inputs = list(map(os.path.abspath, args.inputs))
destinations = list(map(os.path.abspath, args.destinations))

if len(inputs) != len(destinations):
    print('inputs length does not match destinations length')
    sys.exit(1)

for input in inputs:
    subprocess.call(['./apply.sh', input, '--device=gpu'])

print('complete')