#!/usr/bin/env bash

if [ -f {{ dnsmasq_pid_file }} ]; then
   sudo kill -9 $(cat {{ dnsmasq_pid_file }})
   sudo rm {{ dnsmasq_pid_file }}
fi

sudo ip link del {{ vxlan_intf_name }}
sudo ip link del {{ bridge }}

