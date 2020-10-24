import subprocess
import argparse
import os
import shutil
import sys
import datetime

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

status = {}
for i in range(len(inputs)):
    input = inputs[i]
    destination = destinations[i]
    tmpname = tmpnames[i]

    os.symlink(input, os.path.join('tmp', tmpname))

    proc = subprocess.Popen(
        ['./apply.sh', os.path.abspath(os.path.join('tmp', tmpname)), '--device=gpu', '--batch=8'],
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE
    )
    (stdout, stderr) = proc.communicate()
    print(stdout)
    print(stderr, file = sys.stderr)

    output = os.path.join('voice-type-classifier/output_voice_type_classifier', os.path.splitext(os.path.basename(tmpname))[0], 'all.rttm')

    success = False
    if os.path.exists(output):
        shutil.copy(output, destination)
        success = True

    status[destination] = {
        'error': stderr,
        'success': success,
        'datetime': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    open('output.csv', 'a+').write("{},{},{},{}\n".format(destination, status[destination]['datetime'], status[destination]['success'], status[destination]['error']))
