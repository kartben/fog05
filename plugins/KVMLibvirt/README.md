KVM Libvirt plugin

This plugin allow fog05 to manage vm

supported operation:
- deploy
- migrate
- destroy
- stop
- pause
- resume

todo:

- scale of vm

---
package dependencies:

- libvirt-bin
- libvirt-dev
- mkisofs
- seabios
- python3-libvirt
---

python dependencies:

- libvirt-python
- jinja2 
- wget
- qemu-img
- mkisofs


---

config dependencies:

- in `/etc/libvirt/qemu.conf` user and group should be set in a way that the agent can read log files (eg. user = 
ubuntu, group = libvirtd)
- in `/etc/default/libvirt-bin` uncomment libvirtd_opts and modity to libvirtd_opts="-l -d"
- in `/etc/libvirt/libvirtd.conf` set and uncomment listen_tls = 0 and listen_tcp = 1