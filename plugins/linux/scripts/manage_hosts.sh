#!/bin/bash

# PATH TO YOUR HOSTS FILE
hostsFile=/etc/hosts

# IP FOR HOSTNAME
#IP=$2

# Hostname to add/remove.
#HOSTNAME=$1


usage () {
    echo "Usage $0 [-a|-d] [hostname] <ip address>"
    exit 1
}


yell() { echo "$0: $*" >&2; }
die() { yell "$*"; exit 111; }
try() { "$@" || die "cannot $*"; }


removehost () {
    if [ -n "$(grep -w "$hostname$" /etc/hosts)" ]; then
        echo "$hostname found in $hostsFile. Removing now...";
        try sudo sed -ie "/.$hostname$/d" "$hostsFile";
    else
        yell "$hostname was not found in $hostsFile";
    fi

}

addhost () {
    if [ -n "$(grep -w "$hostname$" /etc/hosts)" ]; then
        yell "$hostname, already exists: $(grep $hostname $hostsFile)";
    else
        echo "Adding $hostname to $hostsFile...";
        try printf "%s\t%s\n" "$ip" "$hostname" | sudo tee -a "$hostsFile" > /dev/null;

        if [ -n "$(grep -w "$hostname$" /etc/hosts)" ]; then
            echo "$hostname was added succesfully:";
            echo "$(grep -w "$hostname$" /etc/hosts)";
        else
            die "Failed to add $hostname";
        fi
    fi
}

if [[ $EUID -ne 0 ]]; then
  echo "Please run as root"
  exit 1
fi
if [ $# -lt 2 ]; then
    usage
fi


case $1 in
    -d)
        hostname=$2
        removehost
        exit 0
    ;;
    -a)
        if [ $# -eq 3 ]; then
            hostname=$2
                ip=$3
                addhost
                exit 0
            else
                echo "When add (-a) ip address is necessary!!"
                exit 1
            fi
    ;;
    *)
        echo "$1 wrong parameter"
        usage
    ;;
esac
