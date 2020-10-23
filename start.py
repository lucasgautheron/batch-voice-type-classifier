from ChildProject.projects import ChildProject
import argparse
import sys
import pandas as pd
import subprocess
import os
import wave
import time
import datetime

parser = argparse.ArgumentParser(description='')
parser.add_argument("--source", help = "path to project", required = True)
parser.add_argument("--profile", help = "audio profile to be used", default = "", required = False)
args = parser.parse_args()

project = ChildProject(args.source)
errors, warnings = project.validate_input_data()

if len(errors) > 0:
    print("validation failed, {} error(s) occured".format(len(errors)), file = sys.stderr)
    sys.exit(1)

audio_prefix = os.path.join('converted_recordings', args.profile) if args.profile else 'recordings'
recordings = project.recordings
recordings['exists'] = recordings['filename'].map(lambda f: os.path.exists(os.path.join(project.path, audio_prefix, f)))
recordings = recordings[recordings['exists'] == True]

def get_audio_duration(filename):
    f = wave.open(filename,'r')
    return f.getnframes() / float(f.getframerate())

recordings['duration'] = recordings['filename'].map(lambda f:
    get_audio_duration(os.path.join(project.path, audio_prefix, f))
)
# GPU computation time upper bound according to https://docs.google.com/presentation/d/1JTM_e56RSCpHqzq0VDu8Qude7P5UNKM6v18LT4jI7Do/edit#slide=id.ga0712b0b07_0_16
recordings['vtc_computation_time_estimate'] = recordings['duration'] * 0.57/20 * 4
target_computation_time = 20*3600
batches = recordings['vtc_computation_time_estimate'].sum()/target_computation_time
recordings['batch'] = (recordings.index/batches).astype(int)

print('splitting task in {} jobs'.format(batches))

# do the splitting by child_id for now
for group, group_recordings in recordings.groupby('batch'):
    inputs = group_recordings['filename'].map(lambda f: os.path.join(project.path, audio_prefix, f)).tolist()
    destinations = group_recordings['filename'].map(lambda f: os.path.join(project.path, 'raw_annotations/vtc', f + '.rttm')).tolist()
    tmpnames = group_recordings['filename'].map(lambda s: datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '_' + s.replace('/', '_')).tolist()

    computation_time = group_recordings['vtc_computation_time_estimate'].sum()
    job_name = 'vtc_{}_{}'.format(group, datetime.datetime.now().strftime('%Y%m%d%H%M%S'))

    for destination in destinations:
        os.makedirs(os.path.dirname(destination), exist_ok = True)

    cmd = [
        'sbatch',
        '--partition=gpu',
        '--gres=gpu:1',
        '--job-name=' + job_name,
        '--mem=30G',
        '--time=' + time.strftime("%H:%M:%S", time.gmtime(computation_time)),
        '--output=' + os.path.join(project.path, 'raw_annotations/vtc', job_name + '.out'), 
        '--error=' + os.path.join(project.path, 'raw_annotations/vtc', job_name + '.err'), 
        '--exclude=puck5'

        './run_vtc.sh', '--inputs'
    ] + inputs + ['--destinations'] + destinations + ['--tmpnames'] + tmpnames

    proc = subprocess.Popen(cmd)

    print(" ".join(cmd))
