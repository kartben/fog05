import sys
import os
import uuid
sys.path.append(os.path.join(sys.path[0],'interfaces'))
from States import State
from RuntimePlugin import *
from LibVirtEntity import LibVirtEntity
from jinja2 import Environment
import json
import random

class RuntimeLibVirt(RuntimePlugin):

    def __init__(self, name, version, agent):
        super(RuntimeLibVirt, self).__init__(version)
        self.uuid = uuid.uuid4()
        self.name = name
        self.agent = agent
        self.startRuntime()


        ####### HERE SHOULD REGISTER THE OBSERVER ######

        '''
        ###### test decupling with redis
        import redis
        r = redis.StrictRedis(host='localhost', port=6379)  # Connect to local Redis instance
        self.p = r.pubsub(ignore_subscribe_messages=True)  # See https://github.com/andymccurdy/redis-py/#publish--subscribe
        uri = str('fos://<sys-id>/%s/runtime/%s/entity/*' % (agent.uuid, self.uuid))
        print ("subscribed to %s" % uri)

        self.p.psubscribe(uri)
        import threading
        threading.Thread(target=self.reactToCache, args=(None, None)).start()
        ######
        '''

    def startRuntime(self):

        import libvirt
        self.conn = libvirt.open("qemu:///system")
        return self.uuid


    def stopRuntime(self):
        self.conn.close()

    def getEntities(self):
        return self.currentEntities

    def defineEntity(self, *args, **kwargs):
        """
        Try defining vm
        generating xml from templates/vm.xml with jinja2
        """
        if len(args) > 0:
            entity_uuid = args[4]
            disk_path = str("/opt/fos/%s.qcow2" % entity_uuid)
            cdrom_path = str("/opt/fos/%s_config.iso" % entity_uuid)
            entity = LibVirtEntity(entity_uuid, args[0], args[2], args[1], disk_path, args[3], cdrom_path, [],
                                   args[5], args[6], args[7])
        elif len(kwargs) > 0:
            entity_uuid = kwargs.get('entity_uuid')
            disk_path = str("/opt/fos/disks/%s.qcow2" % entity_uuid)
            cdrom_path = str("/opt/fos/disks/%s_config.iso" % entity_uuid)
            entity = LibVirtEntity(entity_uuid, kwargs.get('name'), kwargs.get('cpu'), kwargs.get('memory'), disk_path,
                                   kwargs.get('disk_size'), cdrom_path, kwargs.get('networks'),
                                   kwargs.get('base_image'), kwargs.get('user-file'), kwargs.get('ssh-key'))
        else:
            return None

        entity.setState(State.DEFINED)
        self.currentEntities.update({entity_uuid: entity})

        return entity_uuid

    def undefineEntity(self, entity_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        entity = self.currentEntities.get(entity_uuid, None)
        if entity is None:
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.DEFINED:
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state",
                                                     str("Entity %s is not in DEFINED state" % entity_uuid))
        else:
            self.currentEntities.pop(entity_uuid,None)
            return True

    def configureEntity(self, entity_uuid):

        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')

        entity = self.currentEntities.get(entity_uuid, None)
        if entity is None:
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.DEFINED:
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state",
                                                     str("Entity %s is not in DEFINED state" % entity_uuid))
        else:

            template_xml = self.agent.getOSPlugin().readFile(os.path.join(sys.path[0], 'plugins', 'RuntimeLibVirt',
                                                                          'templates', 'vm.xml'))

            vm_xml = Environment().from_string(template_xml)
            vm_xml = vm_xml.render(name=entity.name, uuid=entity_uuid, memory=entity.ram,
                                   cpu=entity.cpu, disk_image=entity.disk,
                                   iso_image=entity.cdrom)

            image_name = entity.image.split('/')[-1]

            wget_cmd = str('wget %s -O /opt/fos/images/%s' % (entity.image, image_name))

            conf_cmd = str("%s --hostname %s --uuid %s" % (os.path.join(sys.path[0], 'plugins', 'RuntimeLibVirt',
                                                                   'templates',
                                                                 'create_config_drive.sh'), entity.name, entity_uuid))

            if entity.user_file is not None:
                data_filename = str("userdata_%s" % entity_uuid)
                self.agent.getOSPlugin().storeFile(entity.user_file, "/opt/fos/", data_filename)
                conf_cmd = str(conf_cmd + " --user-data" % data_filename)
            if entity.ssh_key is not None:
                key_filename = str("key_%s.pub" % entity_uuid)
                self.agent.getOSPlugin().storeFile(entity.ssh_key, "/opt/fos/", key_filename)
                conf_cmd = str(conf_cmd + " --ssh-key" % key_filename)

            conf_cmd = str(conf_cmd + " %s" % entity.cdrom)

            qemu_cmd = str("qemu-img create -f qcow2 %s %dG" % (entity.disk, entity.disk_size))

            dd_cmd = str("dd if=/opt/fos/images/%s of=%s" % (image_name, entity.disk))

            entity.image = image_name

            self.agent.getOSPlugin().executeCommand(wget_cmd)
            self.agent.getOSPlugin().executeCommand(qemu_cmd)
            self.agent.getOSPlugin().executeCommand(conf_cmd)
            self.agent.getOSPlugin().executeCommand(dd_cmd)

            self.conn.defineXML(vm_xml)
            entity.onConfigured(vm_xml)
            self.currentEntities.update({entity_uuid: entity})
            return True

    def cleanEntity(self, entity_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')

        entity = self.currentEntities.get(entity_uuid, None)
        if entity is None:
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.CONFIGURED:
            raise StateTransitionNotAllowedException("Entity is not in CONFIGURED state",
                                                     str("Entity %s is not in CONFIGURED state" % entity_uuid))
        else:
            # should undefine on libvirt
            self.lookupByUUID(entity_uuid).undefine()
            ## should remove files (disk, conf drive)
            rm_cmd=str("rm -f %s %s /opt/fos/images/%s /opt/fos/logs/%s_log.log" %
                       (entity.cdrom, entity.disk, entity.image, entity_uuid))
            self.agent.getOSPlugin().executeCommand(rm_cmd)

            entity.onClean()
            self.currentEntities.update({entity_uuid: entity})
            #os.system(rm_cmd)
            return True

    def runEntity(self, entity_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        entity = self.currentEntities.get(entity_uuid,None)
        if entity is None:
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.CONFIGURED:
            raise StateTransitionNotAllowedException("Entity is not in CONFIGURED state",
                                                     str("Entity %s is not in CONFIGURED state" % entity_uuid))
        else:
            self.lookupByUUID(entity_uuid).create()
            entity.onStart()
            self.currentEntities.update({entity_uuid: entity})
            return True

    def stopEntity(self, entity_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        entity = self.currentEntities.get(entity_uuid, None)
        if entity is None:
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.RUNNING:
            raise StateTransitionNotAllowedException("Entity is not in RUNNING state",
                                                     str("Entity %s is not in RUNNING state" % entity_uuid))
        else:
            self.lookupByUUID(entity_uuid).destroy()
            entity.onStop()
            self.currentEntities.update({entity_uuid: entity})
            return True

    def pauseEntity(self, entity_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        entity = self.currentEntities.get(entity_uuid, None)
        if entity is None:
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.RUNNING:
            raise StateTransitionNotAllowedException("Entity is not in RUNNING state",
                                                     str("Entity %s is not in RUNNING state" % entity_uuid))
        else:
            self.lookupByUUID(entity_uuid).suspend()
            entity.onPause()
            self.currentEntities.update({entity_uuid: entity})
            return True

    def resumeEntity(self, entity_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        entity = self.currentEntities.get(entity_uuid,None)
        if entity is None:
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.PAUSED:
            raise StateTransitionNotAllowedException("Entity is not in PAUSED state",
                                                     str("Entity %s is not in PAUSED state" % entity_uuid))
        else:
            self.lookupByUUID(entity_uuid).resume()
            entity.onResume()
            self.currentEntities.update({entity_uuid: entity})
            return True

    def reactToCache(self, key, value, v):
        '''
        import time
        while True:
            #print("Waiting for messages on cache...")
            message = self.p.get_message()  # Checks for message
            if message is None or message.get('type') != 'pmessage':
                time.sleep(1)
            else:
                print (message)
                key = message.get('channel').decode()
                value = message.get('data').decode()
        '''
        uuid = key.split('/')[-1]
        value = json.loads(value)
        action = value.get('status')
        entity_data = value.get('entity_data')
        react_func = self.react(action)
        if react_func is not None and entity_data is None:
            react_func(uuid)
        elif react_func is not None:
            entity_data.update({'entity_uuid': uuid})
            if action == 'define':
                react_func(**entity_data)
            else:
                react_func(entity_data)

    def randomMAC(self):
        mac = [0x00, 0x16, 0x3e,
               random.randint(0x00, 0x7f),
               random.randint(0x00, 0xff),
               random.randint(0x00, 0xff)]
        return ':'.join(map(lambda x: "%02x" % x, mac))

    def lookupByUUID(self, uuid):
        domains = self.conn.listAllDomains(0)
        if len(domains) != 0:
            for domain in domains:
                if str(uuid) == domain.UUIDString():
                    return domain
        else:
            return None

    def react(self, action):
        r = {
            'define': self.defineEntity,
            'configure': self.configureEntity,
            'clean': self.cleanEntity,
            'undefine': self.undefineEntity,
            'stop': self.stopEntity,
            'resume': self.resumeEntity,
            'run': self.runEntity
        }

        return r.get(action, None)
