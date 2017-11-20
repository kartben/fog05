#!/usr/bin/env bash

#sudo brctl addbr {{ bridge_name }}
WAN=$(awk '$2 == 00000000 { print $1 }' /proc/net/route)

sudo ip link add {{ bridge_name }} type bridge
sudo ip link add name {{ vxlan_intf_name }} type vxlan id {{ group_id }} group {{ mcast_group_address }} dstport 4789 dev $WAN
sudo ip link set dev {{ vxlan_intf_name }} master {{ bridge_name }}
#sudo brctl addif  {{ bridge_name }} {{ vxlan_intf_name }}
#sudo brctl stp  {{ bridge_name }} off
sudo ip link set up dev {{ bridge_name }}
sudo ip link set up dev {{ vxlan_intf_name }}

#this should be done on all nodes, or all nodes that have entity on that network
#uses multicast how to do with nodes in differents subnets?
#


### use ip for bridge creation