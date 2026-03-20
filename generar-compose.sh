#!/bin/bash

OUTPUT_FILE=$1
CLIENTS=$2

echo "Generando compose en $OUTPUT_FILE con $CLIENTS clientes..."

python3 generador.py $OUTPUT_FILE $CLIENTS