#!/bin/sh
DATA_DIR=data

# === Check for dirs first and get errors out of the way ===
if [ -d "${DATA_DIR}" ]; then
  echo ${DATA_DIR} ' exists. Please delete it to continue'
  exit 1
fi

echo "Creating data folder"
mkdir -p DATA_DIR

echo "Downloading data"
wget https://www.openslr.org/resources/12/test-clean.tar.gz

echo "Extracting data"
tar -xvf test-clean.tar.gz -C DATA_DIR /
