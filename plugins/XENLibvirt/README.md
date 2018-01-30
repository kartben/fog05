XEN Libvirt plugin

This plugin allow fog05 to manage vm on xen
This uses libvirt to manage a xen hypervisor


supported operation:
- destroy
- stop
- pause
- resume
- deploy

todo:

- scale of vm

- migrate


---
package dependencies:

- libvirt-bin
- libvirt-dev
- mkisofs
- seabios
- python3-libvirt
- xen-hypervisor
- wget
- qemu-img
- mkisofs
---

python dependencies:

- libvirt-python
- jinja2 



---

config dependencies:

- in `/etc/default/libvirt-bin` uncomment libvirtd_opts and modity to libvirtd_opts="-l -d"
- in `/etc/libvirt/libvirtd.conf` set and uncomment listen_tls = 0 and listen_tcp = 1