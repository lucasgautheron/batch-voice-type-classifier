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
parser.add_argument("--mem", help = "slurm jobs memory in GB", default = 30, type = int)
parser.add_argument("--batch", default = 8, type = int)
parser.add_argument("--overwrite", help = "overwrite rttm if exists", default = False, required = False)
parser.add_argument("--recordings", help = "recordings whitelist", default = [], nargs = '+')
args = parser.parse_args()

project = ChildProject(args.source)
errors, warnings = project.validate()

if len(errors) > 0:
    print("validation failed, {} error(s) occured".format(len(errors)), file = sys.stderr)
    sys.exit(1)

audio_prefix = os.path.join('recordings/converted', args.profile) if args.profile else 'recordings/raw'

recordings = project.recordings

if args.recordings:
    recordings = recordings[recordings['recording_filename'].isin(args.recordings)]

if args.profile:
    converted = pd.read_csv(os.path.join(project.path, audio_prefix, 'recordings.csv'))
    recordings = recordings.merge(converted, left_on = 'recording_filename', right_on = 'original_filename')
    recordings['input'] = recordings['converted_filename'].map(lambda f: os.path.join(project.path, audio_prefix, f))
else:
    recordings['input'] = recordings['recording_filename'].map(lambda f: os.path.join(project.path, audio_prefix, f))

recordings['exists'] = recordings['input'].map(lambda f: os.path.exists(f))
print(recordings)
recordings = recordings[recordings['exists'] == True]

def get_audio_duration(filename):
    f = wave.open(filename,'r')
    return f.getnframes() / float(f.getframerate())

recordings['duration'] = recordings['input'].map(lambda f:
    get_audio_duration(f)
)

recordings['destination'] = recordings['recording_filename'].map(lambda f: os.path.join(project.path, 'annotations/vtc/raw', os.path.splitext(f)[0] + '.rttm'))
recordings['tmpname'] = recordings['recording_filename'].map(lambda s: datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '_' + s.replace('/', '_')[:-3] + 'wav')

if not args.overwrite:
    recordings['rttm_exists'] = recordings['destination'].apply(os.path.exists)
    recordings = recordings[recordings['rttm_exists'] == False]

recordings.reset_index(inplace = True)

# GPU computation time upper bound according to https://docs.google.com/presentation/d/1JTM_e56RSCpHqzq0VDu8Qude7P5UNKM6v18LT4jI7Do/edit#slide=id.ga0712b0b07_0_16
recordings['vtc_computation_time_estimate'] = recordings['duration'] * 0.57/20 * 6
target_computation_time = 2*3600
batches = recordings['vtc_computation_time_estimate'].sum()/target_computation_time
recordings['batch'] = (batches*recordings.index/recordings.shape[0]).astype(int)

print('splitting task in {} jobs'.format(batches))

for group, group_recordings in recordings.groupby('batch'):
    computation_time = group_recordings['vtc_computation_time_estimate'].sum()
    job_name = 'vtc_{}_{}'.format(group, datetime.datetime.now().strftime('%Y%m%d%H%M%S'))

    for destination in group_recordings['destination'].tolist():
        os.makedirs(os.path.dirname(destination), exist_ok = True)      

    cmd = [
        'sbatch',
        '--partition=gpu',
        '--gres=gpu:1',
        '--job-name=' + job_name,
        '--mem={}G'.format(args.mem),
        '--time=' + time.strftime("%H:%M:%S", time.gmtime(computation_time)),
        '--output=' + os.path.join(project.path, 'annotations/vtc/raw', job_name + '.out'), 
        '--error=' + os.path.join(project.path, 'annotations/vtc/raw', job_name + '.err'),
        './run_vtc.py', '--inputs'
    ] + group_recordings['input'].tolist() + ['--destinations'] + group_recordings['destination'].tolist() + ['--tmpnames'] + group_recordings['tmpname'].tolist() + ['--batch', str(args.batch)]

    proc = subprocess.Popen(cmd)

    print(" ".join(cmd))
