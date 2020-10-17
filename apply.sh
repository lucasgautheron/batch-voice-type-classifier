#!/bin/bash

/shared/apps/anaconda3/etc/profile.d/conda.sh
conda activate pyannote_vtc

cd voice_type_classifier
./apply "$@"
