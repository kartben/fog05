#!/bin/bash

# PATH TO YOUR HOSTS FILE
ETC_HOSTS=/etc/hosts

# IP FOR HOSTNAME
#IP=$2

# Hostname to add/remove.
#HOSTNAME=$1


usage () {
    echo "Usage $0 [-a|-d] [hostname] <ip address>"
    exit 1
}

removehost () {
    if [ -n "$(grep $HOSTNAME /etc/hosts)" ]
    then
        echo "$HOSTNAME Found in your $ETC_HOSTS, Removing now...";
        sudo sed -i".bak" "/$HOSTNAME/d" $ETC_HOSTS
    else
        echo "$HOSTNAME was not found in your $ETC_HOSTS";
    fi
}

addhost () {
    HOSTS_LINE="$IP\t$HOSTNAME"
    if [ -n "$(grep $HOSTNAME /etc/hosts)" ]
        then
            echo "$HOSTNAME already exists : $(grep $HOSTNAME $ETC_HOSTS)"
        else
            echo "Adding $HOSTNAME to your $ETC_HOSTS";
            sudo -- sh -c -e "echo '$HOSTS_LINE' >> /etc/hosts";

            if [ -n "$(grep $HOSTNAME /etc/hosts)" ]
                then
                    echo "$HOSTNAME was added succesfully: $(grep $HOSTNAME /etc/hosts)";
                else
                    echo "Failed to Add $HOSTNAME, Try again!";
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
        HOSTNAME=$2
        removehost
        exit 0
    ;;
    -a)
        if [ $# -eq 3 ]; then
            HOSTNAME=$2
                IP=$3
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
