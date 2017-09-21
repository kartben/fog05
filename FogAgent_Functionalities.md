# FogAgent Functionalities

- Provide state of the agent (CPU,RAM,Network,Disk,I/O,Arch,Position [GPS Coordinates])
- Start/Stop of native applications
- Managment of µServices (current status,configuration,deploy,relation changes,scaling,migration,shutdown)
- Managment of containers (via Docker/Kuberentes/LXC/LXD API)
- Managment of VM/Unikernels (via libvirt, support migration)
- Advertising and discovery of other agents (should come free thanks to DDS)
- Dashboard (eg. a operator pc can have an agent that discover the FogAgent and provide a simple url for accessing the dashboard)

All these functionalities should be exposed by API