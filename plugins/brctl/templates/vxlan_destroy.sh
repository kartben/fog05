#!/usr/bin/env bash

sudo ip link del {{ vxlan_intf_name }}
sudo ip link del {{ bridge }}

