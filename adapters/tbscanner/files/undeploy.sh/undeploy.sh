#!/bin/sh
ADAPTERROOTFOLDER=/usr/local/bin/adapters
ADAPTERNAME=tbscanner
ADAPTERFULLPATH=$ADAPTERROOTFOLDER/$ADAPTERNAME
ADAPTERSERVICENAME=tbscannermonitor.service
SYSTEMDPATH=/lib/systemd/system
SERVICENAME="Tbscanner Monitor Service"
PYTHONBIN=/usr/bin/python

#Clean up any old adapter stuff
echo "------Cleaning Up Old Adapter Configurations"
sudo systemctl stop $ADAPTERSERVICENAME
sudo systemctl disable $ADAPTERSERVICENAME
sudo rm $SYSTEMDPATH/$ADAPTERSERVICENAME
sudo rm -rf $ADAPTERFULLPATH

echo "------Reloading daemon"
sudo systemctl daemon-reload
