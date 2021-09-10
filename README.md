## Batch voice-type-classifier

Run the Voice Type Classifier over a corpus of daylong recordings on Oberon.

### Installation

Whether you install this repository with `git clone` or `datalad install`, please use the `--recursive` flag to install
the Voice Type Classifier as a submodule.

Then, create the `pyannote` conda environment:

```bash
cd batch_voice_type_classifier/voice_type_classifier
conda env create -f vtc.yml
```

### Usage

```bash
$ python start.py --help
usage: start.py [-h] --source SOURCE [--profile PROFILE] [--mem MEM] [--batch BATCH] [--overwrite OVERWRITE] [--recordings RECORDINGS [RECORDINGS ...]]

optional arguments:
  -h, --help            show this help message and exit
  --source SOURCE       path to project
  --profile PROFILE     audio profile to be used
  --mem MEM             slurm jobs memory in GB
  --batch BATCH
  --overwrite OVERWRITE
                        overwrite rttm if exists
  --recordings RECORDINGS [RECORDINGS ...]
                        recordings whitelist
```

Example:

```bash
python start.py --source ../data/vanuatu --profile standard --recordings ../data/vanuatu/recordings/raw/child9*.WAV
```

You can check that the VTC is running with `squeue`.
