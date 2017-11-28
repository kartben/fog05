LXD plugin

This plugin allow fog05 to manage lxd container

supported operation:


todo:

- scale of vm
- deploy
- migrate
- destroy
- stop
- pause
- resume

---
package dependencies:

- lxd
- lxd-client
---

python dependencies:

- pylxd
- packaging
- jinja2


---

config dependencies:



WARNING:

if you use lxd from snap
https://github.com/lxc/pylxd/issues/257
export LXD_DIR=/var/snap/lxd/common/lxd/



