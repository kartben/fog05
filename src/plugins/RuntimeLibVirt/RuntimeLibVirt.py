import sys
import os
import uuid
sys.path.append(os.path.join(sys.path[0],'interfaces'))
from States import State
from RuntimePlugin import *
from LibVirtEntity import LibVirtEntity
from jinja2 import Environment



class RuntimeLibVirt(RuntimePlugin):

    def __init__(self,name,version,agent):
        super(RuntimeLibVirt, self).__init__(version)
        self.uuid = uuid.uuid4()
        self.name = name
        self.agent = agent


    def startRuntime(self):

        import libvirt

        self.conn=libvirt.open("qemu:///system")
        return self.uuid


    def stopRuntime(self):
        self.conn.close()

    def getEntities(self):
        return self.currentEntities

    def defineEntity(self, *args):
        """
         Try defining vm
         generating xml from templates/vm.xml with jinja2
        """

        entity_uuid = args[4]

        disk_path = str("/opt/fog/%s.qcow2" % entity_uuid)
        cdrom_path = str("/opt/fog/%s_config.iso" % entity_uuid)

        #is defined 
        entity = LibVirtEntity(entity_uuid, args[0], args[2], args[1], disk_path, args[3], cdrom_path, [])
        entity.setState(State.DEFINED)
        self.currentEntities.update({entity_uuid: entity})

        return entity_uuid

    def undefineEntity(self, entity_uuid):
        entity = self.currentEntities.get(entity_uuid, None)
        if entity is None:
            raise EntityNotExistingException("Enitity not existing", str("Entity %s not in runtime %s" % (
                entity_uuid, self.uuid)))
        elif entity.getState() != State.DEFINED:
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state", str("Entity %s is not in "
                                                                                           "DEFINED state" %
                                                                                           entity_uuid))
        else:
            self.currentEntities.pop(entity_uuid,None)
            return True

    def configureEntity(self,entity_uuid):
        entity = self.currentEntities.get(entity_uuid, None)
        if entity is None:
            raise EntityNotExistingException("Enitity not existing", str("Entity %s not in runtime %s" % (
                entity_uuid, self.uuid)))
        elif entity.getState() != State.DEFINED:
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state", str("Entity %s is not in "
                                                                                           "DEFINED state" %
                                                                                           entity_uuid))
        else:

            template_xml = self.agent.getOSPlugin().readFile(os.path.join(sys.path[0], 'plugins', 'RuntimeLibVirt',
                                                                        'templates', 'vm.xml'))

            vm_xml = Environment().from_string(template_xml)
            vm_xml = vm_xml.render(name=entity.name, uuid=entity_uuid, memory=entity.ram,
                                   cpu=entity.cpu, disk_image=entity.disk,
                                   iso_image=entity.cdrom)

            conf_cmd = str("%s --hostname %s %s" % (os.path.join(sys.path[0], 'plugins', 'RuntimeLibVirt', 'templates',
                                                                 'create_config_drive.sh'), entity.name, entity.cdrom))

            qemu_cmd = str("qemu-img create -f qcow2 %s %dG" % (entity.disk, entity.disk_size))
            dd_cmd = str("dd if=/opt/fog/images/%s of=/opt/fog/%s" % ('image', entity.disk))


            self.agent.getOSPlugin().executeCommand(qemu_cmd)
            self.agent.getOSPlugin().executeCommand(conf_cmd)
            self.agent.getOSPlugin().executeCommand(dd_cmd)

            #print(vm_xml)
            self.conn.defineXML(vm_xml)
            entity.onConfigured(vm_xml)
            self.currentEntities.update({entity_uuid: entity})
            return True

    def cleanEntity(self, entity_uuid):
        entity = self.currentEntities.get(entity_uuid, None)
        if entity is None:
            raise EntityNotExistingException("Enitity not existing", str("Entity %s not in runtime %s" % (entity_uuid,
                                                                                                         self.uuid)))
        elif entity.getState() != State.CONFIGURED:
            raise StateTransitionNotAllowedException("Entity is not in CONFIGURED state", str("Entity %s is not in  "
                                                                                             "CONFIGURED state"  %
                                                                                             entity_uuid))
        else:
            # should undefine on libvirt
            self.lookupByUUID(entity_uuid).undefine()
            ## should remove files (disk, conf drive)
            rm_cmd=str("rm -f %s %s" % (entity.cdrom, entity.disk))
            self.agent.getOSPlugin().executeCommand(rm_cmd)

            entity.onClean()
            self.currentEntities.update({entity_uuid: entity})
            #os.system(rm_cmd)
            return True

    def stopEntity(self, entity_uuid):
        entity = self.currentEntities.get(entity_uuid, None)
        if entity is None:
            raise EntityNotExistingException("Enitity not existing", str("Entity %s not in runtime %s" % (entity_uuid,
                                                                                                         self.uuid)))
        elif entity.getState() != State.RUNNING:
            raise StateTransitionNotAllowedException("Entity is not in RUNNING state", str("Entity %s is not in "
                                                                                          "RUNNING state"
                                                                                          % entity_uuid))
        else:
            self.lookupByUUID(entity_uuid).destroy()
            entity.onStop()
            self.currentEntities.update({entity_uuid: entity})
            return True

    def pauseEntity(self, entity_uuid):
        entity = self.currentEntities.get(entity_uuid,None)
        if entity is None:
            raise EntityNotExistingException("Enitity not existing", str("Entity %s not in runtime %s" % (entity_uuid,
                                                                                                         self.uuid)))
        elif entity.getState() != State.RUNNING:
            raise StateTransitionNotAllowedException("Entity is not in RUNNING state", str("Entity %s is not in "
                                                                                          "RUNNING state"
                                                                                          % entity_uuid))
        else:
            self.lookupByUUID(entity_uuid).suspend()
            entity.onPause()
            self.currentEntities.update({entity_uuid: entity})
            return True

    def resumeEntity(self, entity_uuid):
        entity = self.currentEntities.get(entity_uuid,None)
        if entity is None:
            raise EntityNotExistingException("Enitity not existing", str("Entity %s not in runtime %s" % (entity_uuid,
                                                                                                         self.uuid)))
        elif entity.getState() != State.PAUSED:
            raise StateTransitionNotAllowedException("Entity is not in PAUSED state", str("Entity %s is not in PAUSED "
                                                                                         "state" % entity_uuid))
        else:
            self.lookupByUUID(entity_uuid).resume()
            entity.onResume()
            self.currentEntities.update({entity_uuid: entity})
            return True

    def lookupByUUID(self,uuid):
        domains = self.conn.listAllDomains(0)
        if len(domains) != 0:
            for domain in domains:
                if str(uuid) == domain.UUIDString():
                    return domain
        else:
            return None
