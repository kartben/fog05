#!/usr/bin/env bash

#  load_plugins.sh
#
#
#  Created by Gabriele Baldoni on 08/12/17.
#  Example that load plugins in two differents nodes


fos node -u 53712df296494a21be2e80eed00ff9ce -p -a -m ~/Workspace/fog05/plugins/KVMLibvirt/kvm_plugin.json
fos node -u 84610ec8a5424b67a776d5d79e904ff7 -p -a -m ~/Workspace/fog05/plugins/KVMLibvirt/kvm_plugin.json

fos node -u 84610ec8a5424b67a776d5d79e904ff7 -p -a -m ~/Workspace/fog05/plugins/LXD/lxd_plugin.json
fos node -u 53712df296494a21be2e80eed00ff9ce -p -a -m ~/Workspace/fog05/plugins/LXD/lxd_plugin.json

fos node -u 84610ec8a5424b67a776d5d79e904ff7 -p -a -m ~/Workspace/fog05/plugins/brctl/brctl_plugin.json
fos node -u 53712df296494a21be2e80eed00ff9ce -p -a -m ~/Workspace/fog05/plugins/brctl/brctl_plugin.json
