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

---

with centos7 we hit [this bug](https://bugs.centos.org/view.php?id=10608)