#!/bin/bash

# If this script is executed, we know the adapter has been deployed. No need to test for that.
STATUS="Deployed"

ADAPTERROOTFOLDER=/usr/local/bin/adapters
ADAPTERNAME=thunderboard
ADAPTERFULLPATH=$ADAPTERROOTFOLDER/$ADAPTERNAME
PYTHONFILE=scanner.py

TARGETS=("$ADAPTERFULLPATH/$PYTHONFILE")
for target in "${TARGETS[@]}"
do
      PID=$(ps aux | grep -v grep | grep $target | awk '{print $2}')
      #echo $PID
		if [[ $PID ]]; then
		    STATUS="Running $PID"
		else
		    STATUS="Stopped"
		fi

echo $STATUS
done