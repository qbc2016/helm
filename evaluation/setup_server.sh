#!bin/bash

set -e
 
SUITE_NAME=test
PORT=8000

while getopts "n:p:" flag
do
    # shellcheck disable=SC2220
    case "${flag}" in
        n) SUITE_NAME=${OPTARG};;
        p) PORT=${OPTARG};;
    esac
done

PATH_HELM=/root/src/crfm-helm
PATH_WORKDIR=/root/src/crfm-helm


cd ${PATH_WORKDIR}

export PYTHONPATH=$PYTHONPATH:${PATH_HELM}/src/

/root/miniconda3/bin/python ${PATH_HELM}/src/helm/benchmark/presentation/summarize.py \
        --suite ${SUITE_NAME}

/root/miniconda3/bin/python ${PATH_HELM}/src/helm/benchmark/server.py -o ${PATH_WORKDIR}/benchmark_output -p ${PORT}
