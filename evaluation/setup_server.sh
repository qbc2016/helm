#!bin/bash

set -e
 
SUITE_NAME=test_nl2sql

PATH_HELM=/root/src/helm
PATH_WORKDIR=/root/src/helm


cd ${PATH_WORKDIR}

export PYTHONPATH=$PYTHONPATH:${PATH_HELM}/src/

/root/miniconda3/bin/python ${PATH_HELM}/src/helm/benchmark/presentation/summarize.py \
        --suite ${SUITE_NAME}

/root/miniconda3/bin/python ${PATH_HELM}/src/helm/benchmark/server.py -o ${PATH_WORKDIR}/benchmark_output -p 8088
