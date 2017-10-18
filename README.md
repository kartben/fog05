#FogOS

python packages dependencies:

- psutil
- libvirt-python
- netifaces

---
package dependencies:

    - libvirt          |--> KVM Plugin
    - libvirt devel    |  user should be in libvirt and kvm groups
    - mkisofs          |
    - seabios          |
    
    - bridge-utils     |-> brctl Plugin
---

config dependencies:

- user should be able to use sudo without password asking (`echo "username  ALL=(ALL) NOPASSWD: ALL"  >> /etc/sudoers`)
- in `/etc/libvirt/qemu.conf` user and group should be set in a way that the agent can read log files (eg. user = 
ubuntu, group = libvirtd)
---

with centos7 we hit [this bug](https://bugs.centos.org/view.php?id=10608)