KVM Libvirt plugins


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

---

config dependencies:

- in `/etc/libvirt/qemu.conf` user and group should be set in a way that the agent can read log files (eg. user = 
ubuntu, group = libvirtd)
- in `/etc/defaul/libvirt-bin` uncomment libvirtd_opts and modity to libvirtd_opts="-l -d"
- in `/etc/libvirt/libvirtd.conf` set and uncomment listen_tls = 0 and listen_tcp = 1