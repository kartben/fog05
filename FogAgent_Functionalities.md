# FogAgent Functionalities

- Provide state of the agent (CPU,RAM,Network,Disk,I/O,Arch,Position [GPS Coordinates])

		@AC: In general we need to provide monitoring of nodes as well as 
		deployed entities.
		 	
- Start/Stop of native applications
- Managment of µServices (current status,configuration,deploy,relation changes,scaling,migration,shutdown)
- Managment of containers (via Docker/Kuberentes/LXC/LXD API)
- Managment of VM/Unikernels (via libvirt, support migration)
- Advertising and discovery of other agents (should come free thanks to DDS)
- Dashboard (eg. a operator pc can have an agent that discover the FogAgent and provide a simple url for accessing the dashboard)

		@AC: Eventually we also want to provide node-related functionalities, 
		such as software update, etc.
		
		The other question to address -- relevant for our collaboration with Intel -- 
		is node identity. 
		
All these functionalities should be exposed by API

		@AC: We should also list the network-releated control features 
		that will eventually be provided. Then we'll do a roadmap to
		describe what will be the intial focus.