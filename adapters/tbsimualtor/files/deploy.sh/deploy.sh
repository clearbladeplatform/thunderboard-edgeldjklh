#!/bin/bash
#Variables
ADAPTERROOTFOLDER=/usr/local/bin/adapters
ADAPTERNAME=tbscanner
ADAPTERFULLPATH=$ADAPTERROOTFOLDER/$ADAPTERNAME
ADAPTERSERVICENAME=tbscannermonitor.service
SYSTEMDPATH=/lib/systemd/system
PYTHONFILE=tbscanner.py
SERVICENAME="Tbscanner Monitor Service"
PYTHONBIN=/usr/bin/python
NETWORKSERVICENAME="clearbladenetwork2.service"

#Clean up any old adapter stuff
echo "------Cleaning Up Old Adapter Configurations"
sudo systemctl stop $ADAPTERSERVICENAME
sudo systemctl disable $ADAPTERSERVICENAME
sudo rm $SYSTEMDPATH/$ADAPTERSERVICENAME
sudo rm -rf $ADAPTERFULLPATH

#Copy adapter assets to appropriate directories
echo "------Creating File Structure"
sudo mkdir $ADAPTERROOTFOLDER
sudo mkdir $ADAPTERFULLPATH

echo "------Moving Adapter Files"
#Move the files to the adapter location
sudo mv *.sh $ADAPTERFULLPATH
sudo mv *.py $ADAPTERFULLPATH

#Ensure files are executable
echo "------Setting Executable Flage"
sudo chmod +x $ADAPTERFULLPATH

#Create a systemd service
echo "------Configuring Service"

sudo cat >$SYSTEMDPATH/$ADAPTERSERVICENAME <<EOF
[Unit]
Description=$ADAPTERSERVICENAME
After=$NETWORKSERVICENAME

[Service]
Type=simple
ExecStart=$PYTHONBIN $ADAPTERFULLPATH/$PYTHONFILE
Restart=on-abort
TimeoutSec=30
RestartSec=30
StartLimitInterval=350
StartLimitBurst=10

[Install]
WantedBy=multi-user.target 
EOF

echo "-----Install Pre-requisite sofware"
#sudo apt-get update
#sudo apt-get -y dist-upgrade 
sudo apt-get install git build-essential libglib2.0-dev -y
git clone https://github.com/IanHarvey/bluepy.git
cd bluepy
python setup.py build
sudo python setup.py install
sudo pip install clearblade

echo "------Reloading daemon"
sudo systemctl daemon-reload

#Enable the adapter to start on reboot Note: remove this if you want to manually maintain the adapter
echo "------Enabling Startup on Reboot"
sudo systemctl enable $ADAPTERSERVICENAME
sudo systemctl start $ADAPTERSERVICENAME

echo "------Thunderboard Adapter Deployed"
