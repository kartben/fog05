#!/usr/bin/env bash

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi


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

echo off
apt update
apt install -y clang unzip git python3 python3-dev python3-pip binutils make
echo on

mkdir $WD/fog

cd $WD/fog

wget  https://www.dropbox.com/s/sixq7bne7yp4yu5/ospl.zip

unzip ospl.zip

cd ospl

wget https://www.dropbox.com/s/7u5vzxjg1ea50us/license.lic -O $WD/fog/license.lic

./P768-VortexOpenSplice-6.8.2b1-HDE-x86_64.linux-gcc5.4.0-glibc2.23-installer.run  --providedLicenseFile $WD/fog/license.lic --mode unattended --prefix $WD/fog/ADLINK

wget https://www.dropbox.com/s/ql9ngtr3zoayp3k/ospl.xml

cp ospl.xml $WD/fog/ADLINK/Vortex_v2/Device/VortexOpenSplice/6.8.2b1/HDE/x86_64.linux/etc/config/ospl.xml

echo "source $WD/fog/ADLINK/Vortex_v2/Device/VortexOpenSplice/6.8.2b1/HDE/x86_64.linux/release.com" >> ~/.profile

source ~/.profile

cd $WD/fog

git clone https://github.com/atolab/pydds

cd pydds

./configure.linux

cp builtin-types/libdython.so $OSPL_HOME/lib


if [ ! -f /etc/machine-id ]; then
   ln -s /var/lib/dbus/machine-id /etc/machine-id
fi

python3 setup.py install --record pydds_files.txt

#cd $WD/fog
#
#git clone https://github.com/atolab/fog05
#
#cd fog05

cd $WD

pip3 install python-daemon psutil netifaces

python3 setup.py install --record fog05_files.txt


