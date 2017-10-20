#FogOS

python packages dependencies:

- psutil
- netifaces
    
    - bridge-utils     |-> brctl Plugin
---

config dependencies:

- user should be able to use sudo without password asking (`echo "username  ALL=(ALL) NOPASSWD: ALL"  >> /etc/sudoers`)

---

with centos7 we hit [this bug](https://bugs.centos.org/view.php?id=10608)