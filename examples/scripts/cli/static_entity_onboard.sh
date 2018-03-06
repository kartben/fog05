#!/usr/bin/env bash


read -n 1 -s -r -p "Press any key to start"

fos node -u 53712df296494a21be2e80eed00ff9ce -p -a -m ../../../plugins/KVMLibvirt/kvm_plugin.json
fos node -u 84610ec8a5424b67a776d5d79e904ff7 -p -a -m ../../../plugins/KVMLibvirt/kvm_plugin.json

fos node -u 84610ec8a5424b67a776d5d79e904ff7 -p -a -m ../../../plugins/LXD/lxd_plugin.json
fos node -u 53712df296494a21be2e80eed00ff9ce -p -a -m ../../../plugins/LXD/lxd_plugin.json

fos node -u 84610ec8a5424b67a776d5d79e904ff7 -p -a -m ../../../plugins/brctl/brctl_plugin.json
fos node -u 53712df296494a21be2e80eed00ff9ce -p -a -m ../../../plugins/brctl/brctl_plugin.json

read -n 1 -s -r -p "Press any key to onboard the entity"

fos entity --add -m ../../manifest/entity.json
