#!/usr/bin/env bash

# sudo -n true
# 0 no password
# something password asked
#if [ "$EUID" -ne 0 ]
#  then echo "Please run as root"
#  exit
#fi


if [ -f /etc/os-release ]; then
    # freedesktop.org and systemd
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
elif type lsb_release >/dev/null 2>&1; then
    # linuxbase.org
    OS=$(lsb_release -si)
    VER=$(lsb_release -sr)
elif [ -f /etc/lsb-release ]; then
    # For some versions of Debian/Ubuntu without lsb_release command
    . /etc/lsb-release
    OS=$DISTRIB_ID
    VER=$DISTRIB_RELEASE
elif [ -f /etc/debian_version ]; then
    # Older Debian/Ubuntu/etc.
    OS=Debian
    VER=$(cat /etc/debian_version)
elif [ -f /etc/SuSe-release ]; then
    # Older SuSE/etc.
    ...
elif [ -f /etc/redhat-release ]; then
    # Older Red Hat, CentOS, etc.
    ...
else
    # Fall back to uname, e.g. "Linux <version>", also works for BSD, etc.
    OS=$(uname -s)
    VER=$(uname -r)
fi

ARCH=$(uname -m)
WD=$(pwd)

echo "Running on $OS $VER $ARCH"
echo "Installing under $WD"

# TODO FIX FOR OTHER DISTRIBUTIONS

if [ ! -f /etc/machine-id ]; then
   ln -s /var/lib/dbus/machine-id /etc/machine-id
fi


sudo apt update
sudo apt install -y unzip git python3 python3-dev python3-pip clang maven openjdk-8-jdk


sudo rm -rf $WD/fog

mkdir $WD/fog
cd $WD/fog

git clone https://github.com/atolab/cdds
cd cdds/src
mkdir build
cd build
cmake ..
make
sudo make install
cd $WD/fog
wget https://www.dropbox.com/s/0bgnw8to4ojg5jv/vortexdds.xml -O cyclonedds.xml
sudo mkdir -p /usr/local/etc/CycloneDDS/
sudo cp cyclonedds.xml /usr/local/etc/CycloneDDS/
sudo chmod a+r /usr/local/etc/CycloneDDS/cyclonedds.xml
sudo chmod a+w /usr/local/etc/CycloneDDS/cyclonedds.xml
echo "export VORTEXDDS_URI=file:///usr/local/etc/CycloneDDS/cyclonedds.xml" >> ~/.bash_profile
if [ -f ~/.profile ]; then
   echo "source .profile" >> ~/.bash_profile
fi
source ~/.bash_profile
cd $WD/fog

git clone git@github.com:atolab/python-cdds.git
cd python-cdds
./configure
sudo python3 setup.py install --record pycham_files.txt
cd $WD/fog

git clone git@github.com:atolab/python-dstore.git
cd python-dstore
sudo python3 setup.py install --record dstore_files.txt
cd $WD

pip3 install python-daemon psutil netifaces jinja2

sudo python3 setup.py install --record fog05_files.txt