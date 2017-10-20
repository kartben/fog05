bridge utils plugin

This plugin allow fog05 to manage networks with bridge utils

supported operation:
- create virtual bridge
- create virtual network
- add interface to network
- delete virtual interface
- delete virtual bridge
- delete virtual network

todo:

- create virtual interface
- remove interface from network


---
package dependencies:

- bridge-utils
---


config dependencies:

- user should be able to use sudo without password asking (`echo "username  ALL=(ALL) NOPASSWD: ALL"  >> /etc/sudoers`)
