#!/usr/bin/env bash

#84610ec8a5424b67a776d5d79e904ff7
#53712df296494a21be2e80eed00ff9ce
fos node -u 84610ec8a5424b67a776d5d79e904ff7 -p -a -m ../../../plugins/LXD/lxd_plugin.json
fos node -u 84610ec8a5424b67a776d5d79e904ff7 -p -a -m ../../../plugins/brctl/brctl_plugin.json
fos node -u 84610ec8a5424b67a776d5d79e904ff7 -p -a -m ../../../plugins/KVMLibvirt/kvm_plugin.json

read -n 1 -s -r -p "Press any key to start\n"

fos network -u 84610ec8a5424b67a776d5d79e904ff7 -a -m ../../manifest/network_demo.json

read -n 1 -s -r -p "Press any key to start"
sleep 1

fos entity -u 84610ec8a5424b67a776d5d79e904ff7 --define -m ../../manifest/brain.json
read -n 1 -s -r -p "Press any key to continue..."
fos entity -u 84610ec8a5424b67a776d5d79e904ff7 --define -m ../../manifest/gateway.json

sleep 1
read -n 1 -s -r -p "Press any key to continue..."

fos entity -u 84610ec8a5424b67a776d5d79e904ff7 --configure -eu eecf97d2-64ff-4992-a499-d748038b0535 -iu 1
read -n 1 -s -r -p "Press any key to continue..."
fos entity -u 84610ec8a5424b67a776d5d79e904ff7 --configure -eu 0be550dc-d9c4-11e7-aa21-d3df37fbfcfa -iu 2

read -n 1 -s -r -p "Press any key to continue..."
sleep 1

fos entity -u 84610ec8a5424b67a776d5d79e904ff7 --run -eu 0be550dc-d9c4-11e7-aa21-d3df37fbfcfa -iu 2
read -n 1 -s -r -p "Press any key to continue..."
fos entity -u 84610ec8a5424b67a776d5d79e904ff7 --run -eu eecf97d2-64ff-4992-a499-d748038b0535 -iu 1


read -n 1 -s -r -p "Press any key to continue..."

fos entity -u 84610ec8a5424b67a776d5d79e904ff7 --configure -eu eecf97d2-64ff-4992-a499-d748038b0535 -iu 3
read -n 1 -s -r -p "Press any key to continue..."
fos entity -u 84610ec8a5424b67a776d5d79e904ff7 --configure -eu 0be550dc-d9c4-11e7-aa21-d3df37fbfcfa -iu 4

read -n 1 -s -r -p "Press any key to continue..."
sleep 1

fos entity -u 84610ec8a5424b67a776d5d79e904ff7 --run -eu 0be550dc-d9c4-11e7-aa21-d3df37fbfcfa -iu 4
read -n 1 -s -r -p "Press any key to continue..."
fos entity -u 84610ec8a5424b67a776d5d79e904ff7 --run -eu eecf97d2-64ff-4992-a499-d748038b0535 -iu 3




read -n 1 -s -r -p "Press any key to continue"

fos entity -u 84610ec8a5424b67a776d5d79e904ff7 --stop -eu eecf97d2-64ff-4992-a499-d748038b0535 -iu 1
read -n 1 -s -r -p "Press any key to continue..."
fos entity -u 84610ec8a5424b67a776d5d79e904ff7 --stop -eu 0be550dc-d9c4-11e7-aa21-d3df37fbfcfa -iu 2

read -n 1 -s -r -p "Press any key to continue..."
sleep 1

fos entity -u 84610ec8a5424b67a776d5d79e904ff7 --clean -eu eecf97d2-64ff-4992-a499-d748038b0535 -iu 1
read -n 1 -s -r -p "Press any key to continue..."
fos entity -u 84610ec8a5424b67a776d5d79e904ff7 --clean -eu 0be550dc-d9c4-11e7-aa21-d3df37fbfcfa -iu 2

read -n 1 -s -r -p "Press any key to continue..."
sleep 1

fos entity -u 84610ec8a5424b67a776d5d79e904ff7 --undefine -eu eecf97d2-64ff-4992-a499-d748038b0535
read -n 1 -s -r -p "Press any key to continue..."
fos entity -u 84610ec8a5424b67a776d5d79e904ff7 --undefine -eu 0be550dc-d9c4-11e7-aa21-d3df37fbfcfa
read -n 1 -s -r -p "Press any key to continue..."
sleep 1

fos network -u 84610ec8a5424b67a776d5d79e904ff7 -nu 2c4e946a-ed83-41cd-ac3d-42d8b806f546 -r


sleep 1
read -n 1 -s -r -p "Press any key to exit..."
