#!/bin/bash

source /shared/apps/anaconda3/etc/profile.d/conda.sh
conda init bash
conda activate pyannote

cd voice-type-classifier
./apply.sh "$@"
