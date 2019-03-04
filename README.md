This directory contains everything for the Konekt updater script

dashupdater.py is the actual script and the libs directory contains all
supporting libraries

version.txt contains the version string to use. To prevent any line ending
parsing weirdness, set this value on the command line with:
echo -n "1.0" > version.txt

Run build.sh to create a compiled package for the OS you are on.

To run/build the updater on Ubuntu:
 - sudo apt-get install python-virtualenv python-dev libusb-dev libudev-dev libusb-1.0-0-dev
 - pip install -r requirements.txt

