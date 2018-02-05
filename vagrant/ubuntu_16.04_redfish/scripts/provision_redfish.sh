#!/bin/bash

sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get -y install python3-pip
sudo pip3 install --upgrade pip
sudo pip3 install requests[security]
sudo pip3 install python-redfish
sudo pip3 install python-ilorest-library
if [[ ! -d /home/vagrant/python-ilorest-library ]] ; then
	git clone https://github.com/HewlettPackard/python-ilorest-library.git
	sudo cp /home/vagrant/python-ilorest-library/examples/Redfish/_redfishobject.py /usr/local/lib/python3.5/dist-packages/
fi
