#!/usr/bin/env bash

read -n 1 -s -r -p "Press any key to start"

fos node -u 53712df296494a21be2e80eed00ff9ce -p -a -m ../../../plugins/KVMLibvirt/kvm_plugin.json
fos node -u 84610ec8a5424b67a776d5d79e904ff7 -p -a -m ../../../plugins/KVMLibvirt/kvm_plugin.json

fos node -u 84610ec8a5424b67a776d5d79e904ff7 -p -a -m ../../../plugins/LXD/lxd_plugin.json
fos node -u 53712df296494a21be2e80eed00ff9ce -p -a -m ../../../plugins/LXD/lxd_plugin.json

fos node -u 84610ec8a5424b67a776d5d79e904ff7 -p -a -m ../../../plugins/brctl/brctl_plugin.json
fos node -u 53712df296494a21be2e80eed00ff9ce -p -a -m ../../../plugins/brctl/brctl_plugin.json

read -n 1 -s -r -p "Press any key to deploy network and define&configure entities"

fos network -u 53712df296494a21be2e80eed00ff9ce -a -m ../../manifest/network_demo.json
fos network -u 84610ec8a5424b67a776d5d79e904ff7 -a -m ../../manifest/network_demo.json


sleep 1

fos entity -u 53712df296494a21be2e80eed00ff9ce --define -m ../../manifest/vm.json

fos entity -u 84610ec8a5424b67a776d5d79e904ff7 --define -m ../../manifest/gateway.json

sleep 1

fos entity -u 53712df296494a21be2e80eed00ff9ce --configure -eu 9fa75e6a-d9c3-11e7-b769-5f3db30f0c2e -iu 2ec0bf9a-f6ef-11e7-a780-c3b00c49479c
sleep 1
fos entity -u 84610ec8a5424b67a776d5d79e904ff7 --configure -eu 0be550dc-d9c4-11e7-aa21-d3df37fbfcfa -iu 2

read -n 1 -s -r -p "Press any key to run"

sleep 1

fos entity -u 84610ec8a5424b67a776d5d79e904ff7 --run -eu 0be550dc-d9c4-11e7-aa21-d3df37fbfcfa -iu 2
sleep 1
fos entity -u 53712df296494a21be2e80eed00ff9ce --run -eu 9fa75e6a-d9c3-11e7-b769-5f3db30f0c2e -iu 2ec0bf9a-f6ef-11e7-a780-c3b00c49479c

read -n 1 -s -r -p "Press any key to migrate the vm instance"

fos entity -u 53712df296494a21be2e80eed00ff9ce -eu 9fa75e6a-d9c3-11e7-b769-5f3db30f0c2e -du 84610ec8a5424b67a776d5d79e904ff7 --migrate -iu 2ec0bf9a-f6ef-11e7-a780-c3b00c49479c



read -n 1 -s -r -p "Press any key to stop, undefine and clean entities"

fos entity -u 84610ec8a5424b67a776d5d79e904ff7 --stop -eu 9fa75e6a-d9c3-11e7-b769-5f3db30f0c2e -iu 2ec0bf9a-f6ef-11e7-a780-c3b00c49479c
sleep 1
fos entity -u 84610ec8a5424b67a776d5d79e904ff7 --stop -eu 0be550dc-d9c4-11e7-aa21-d3df37fbfcfa -iu 2


sleep 1

fos entity -u 84610ec8a5424b67a776d5d79e904ff7 --clean -eu 9fa75e6a-d9c3-11e7-b769-5f3db30f0c2e -iu 2ec0bf9a-f6ef-11e7-a780-c3b00c49479c
sleep 1
fos entity -u 84610ec8a5424b67a776d5d79e904ff7 --clean -eu 0be550dc-d9c4-11e7-aa21-d3df37fbfcfa -iu 2

sleep 1

fos entity -u 84610ec8a5424b67a776d5d79e904ff7 --undefine -eu 9fa75e6a-d9c3-11e7-b769-5f3db30f0c2e -iu 2ec0bf9a-f6ef-11e7-a780-c3b00c49479c
sleep 1
fos entity -u 84610ec8a5424b67a776d5d79e904ff7 --undefine -eu 0be550dc-d9c4-11e7-aa21-d3df37fbfcfa -iu 2

sleep 1

fos network -u 53712df296494a21be2e80eed00ff9ce -nu 2c4e946a-ed83-41cd-ac3d-42d8b806f546 -r
sleep 1
fos network -u 84610ec8a5424b67a776d5d79e904ff7 -nu 2c4e946a-ed83-41cd-ac3d-42d8b806f546 -r

sleep 1

echo 'Done!'
