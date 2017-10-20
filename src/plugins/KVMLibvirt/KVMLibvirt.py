import sys
import os
import uuid
sys.path.append(os.path.join(sys.path[0],'interfaces'))
from States import State
from RuntimePlugin import *
from KVMLibvirtEntity import KVMLibvirtEntity
from jinja2 import Environment
import json
import random
import time
import re

class KVMLibvirt(RuntimePlugin):

    def __init__(self, name, version, agent):
        super(KVMLibvirt, self).__init__(version)
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
        uri = str('fos://<sys-id>/%s/runtime/%s/entity/*' % (self.agent.uuid, self.uuid))
        print("KVM Listening on %s" % uri)
        self.agent.store.observe(uri, self.reactToCache)
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
            entity = KVMLibvirtEntity(entity_uuid, args[0], args[2], args[1], disk_path, args[3], cdrom_path, [],
                                   args[5], args[6], args[7])
        elif len(kwargs) > 0:
            entity_uuid = kwargs.get('entity_uuid')
            disk_path = str("/opt/fos/disks/%s.qcow2" % entity_uuid)
            cdrom_path = str("/opt/fos/disks/%s_config.iso" % entity_uuid)
            entity = KVMLibvirtEntity(entity_uuid, kwargs.get('name'), kwargs.get('cpu'), kwargs.get('memory'), disk_path,
                                   kwargs.get('disk_size'), cdrom_path, kwargs.get('networks'),
                                   kwargs.get('base_image'), kwargs.get('user-data'), kwargs.get('ssh-key'))
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

            template_xml = self.agent.getOSPlugin().readFile(os.path.join(sys.path[0], 'plugins', 'KVMLibvirt',
                                                                          'templates', 'vm.xml'))

            vm_xml = Environment().from_string(template_xml)
            vm_xml = vm_xml.render(name=entity.name, uuid=entity_uuid, memory=entity.ram,
                                   cpu=entity.cpu, disk_image=entity.disk,
                                   iso_image=entity.cdrom, networks=entity.networks)
            image_name = entity.image.split('/')[-1]

            wget_cmd = str('wget %s -O /opt/fos/images/%s' % (entity.image, image_name))

            conf_cmd = str("%s --hostname %s --uuid %s" % (os.path.join(sys.path[0], 'plugins', 'KVMLibvirt',
                                                                   'templates',
                                                                 'create_config_drive.sh'), entity.name, entity_uuid))

            rm_temp_cmd = str("rm")
            if entity.user_file is not None:
                data_filename = str("userdata_%s" % entity_uuid)
                self.agent.getOSPlugin().storeFile(entity.user_file, "/opt/fos/", data_filename)
                data_filename = str("/opt/fos/%s" % data_filename)
                conf_cmd = str(conf_cmd + " --user-data %s" % data_filename)
                rm_temp_cmd = str(rm_temp_cmd + " %s" % data_filename)
            if entity.ssh_key is not None:
                key_filename = str("key_%s.pub" % entity_uuid)
                self.agent.getOSPlugin().storeFile(entity.ssh_key, "/opt/fos/", key_filename)
                key_filename = str("/opt/fos/%s" % key_filename)
                conf_cmd = str(conf_cmd + " --ssh-key %s" % key_filename)
                rm_temp_cmd = str(rm_temp_cmd + " %s" % key_filename)

            conf_cmd = str(conf_cmd + " %s" % entity.cdrom)

            qemu_cmd = str("qemu-img create -f qcow2 %s %dG" % (entity.disk, entity.disk_size))

            dd_cmd = str("dd if=/opt/fos/images/%s of=%s" % (image_name, entity.disk))

            entity.image = image_name

            self.agent.getOSPlugin().executeCommand(wget_cmd)
            self.agent.getOSPlugin().executeCommand(qemu_cmd)
            self.agent.getOSPlugin().executeCommand(conf_cmd)
            self.agent.getOSPlugin().executeCommand(dd_cmd)

            if entity.ssh_key is not None or entity.user_file is not None:
                self.agent.getOSPlugin().executeCommand(rm_temp_cmd)

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
            log_filename = str("/opt/fos/logs/%s_log.log" % entity_uuid)
            #self.wait_boot(log_filename)
            '''
            Then after boot should update the `actual store` with the run status of the vm
            '''

            print('booted')
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




    def migrateEntity(self, entity_uuid,  dst=False):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        entity = self.currentEntities.get(entity_uuid, None)
        if entity is None:
            if dst is True:
                print("I'm the destination node")
                '''
                Should wait connection from source node, for cloning disk, and enable libvirt connection
                '''
                self.beforeMigrateEntityActions(entity_uuid, True)

                ## should way for finished migration
                while True:
                    dom = self.lookupByUUID(entity_uuid)
                    if dom is None:
                        print("Domain is non already in this host")
                        time.sleep(10)
                    else:
                        flag = dom.isActive()
                        if flag is True:
                            break
                        else:
                            print('The domain is not running.')
                            time.sleep(10)

                self.beforeMigrateEntityActions(entity_uuid, True)

            else:
                raise EntityNotExistingException("Enitity not existing",
                                                 str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.RUNNING:
            raise StateTransitionNotAllowedException("Entity is not in RUNNING state",
                                                     str("Entity %s is not in RUNNING state" % entity_uuid))
        else:
                print("I'm the source node")
                '''
                Get information about destination node [IP Address] then start live migration
                '''
                self.beforeMigrateEntityActions(entity_uuid)
                self.afterMigrateEntityActions(entity_uuid)


    def beforeMigrateEntityActions(self, entity_uuid, dst=False):
        if dst is True:
            print("I'm the destination node before migration")
            uri = str("fos://<sys-id>/%s/runtime/%s/entity/%s" % (self.agent.uuid, self.uuid, entity_uuid))
            vm_info = json.loads(self.agent.store.get(uri)).get("entity_data")
            disk_path = str("/opt/fos/disks/%s.qcow2" % entity_uuid)
            cdrom_path = str("/opt/fos/disks/%s_config.iso" % entity_uuid)
            entity = KVMLibvirtEntity(entity_uuid, vm_info.get('name'), vm_info.get('cpu'), vm_info.get('memory'),
                                      disk_path,
                                      vm_info.get('disk_size'), cdrom_path, vm_info.get('networks'),
                                      vm_info.get('base_image'), vm_info.get('user-data'), vm_info.get('ssh-key'))
            entity.state = State.LANDING
            '''
            Should not use configuration disk
            '''
            ##create disks
            qemu_cmd = str("qemu-img create -f qcow2 %s %dG" % (entity.disk, entity.disk_size))
            conf_cmd = str("touch %s" % entity.cdrom) #for size should use fstat on real

            self.agent.getOSPlugin().executeCommand(qemu_cmd)
            self.agent.getOSPlugin().executeCommand(conf_cmd)

            self.currentEntities.update({entity_uuid: entity})
            # disk image
            ## create xml template TODO: create method for this and disk creation
            #template_xml = self.agent.getOSPlugin().readFile(os.path.join(sys.path[0], 'plugins', 'KVMLibvirt',
            #                                                              'templates', 'vm.xml'))
            #
            #vm_xml = Environment().from_string(template_xml)
            #vm_xml = vm_xml.render(name=entity.name, uuid=entity_uuid, memory=entity.ram,
            #                       cpu=entity.cpu, disk_image=entity.disk,
            #                       iso_image=entity.cdrom, networks=entity.networks)
            ## This should not be necessary, libvirt migration do all stuff, only need to create the disks,

            return True
        else:
            import libvirt
            time.sleep(5)
            entity = self.currentEntities.get(entity_uuid, None)
            print("I'm the source node before")
            uri = str("fos://<sys-id>/%s/runtime/%s/entity/%s" % (self.agent.uuid, self.uuid, entity_uuid))
            fognode_uuid = json.loads(self.agent.store.get(uri)).get("dst")
            entity.state = State.TAKING_OFF
            uri = str("fos://<sys-id>/%s/" % fognode_uuid)  # TODO: clarify this get
            dst_node_info = json.loads(self.agent.store.get(uri))

            '''
            Should wait for destination node to finish disk initialization and then use libvirt for live migration
            '''

            dom = self.lookupByUUID(entity_uuid)
            nw = dst_node_info.get('network')

            dst_hostname = dst_node_info.get('name')

            dst_ip = [x for x in nw if x.get("inft_configuration").get("ipv4_gateway") != ""]
            # or x.get("inft_configuration").get("ipv6_gateway") for ip_v6
            if len(dst_ip) == 0:
                return False

            dst_ip = dst_ip[0].get("inft_configuration").get("ipv4_address") #as on search should use ipv6

            add_to_hosts = str('sudo -- sh -c -e "echo \'%s    %s\' >> /etc/hosts"' % (dst_ip, dst_hostname))

            self.agent.getOSPlugin().executeOnOS(add_to_hosts)
            # should ask to osplugin to add a know host

            dst_host = str('qemu+ssh://%s/system' % dst_ip)
            print(dst_host)

            dest_conn = libvirt.open(dst_host)
            if dest_conn == None:
                print('Failed to open connection to %s' % dst)
                exit(1)
            #and libvirt.VIR_MIGRATE_PEER2PEER
            new_dom = dom.migrate(dest_conn, libvirt.VIR_MIGRATE_LIVE, None, None, 0)
            if new_dom == None:
                print('Could not migrate to the new domain')
                exit(1)

            print('Domain was migrated successfully.')

            return True
            




    def afterMigrateEntityActions(self, entity_uuid, dst=False):
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
            if dst is True:
                print("I'm the destination node after migration")
                entity.state = State.RUNNING
                self.currentEntities.update({entity_uuid: entity})
                return True
            else:
                print("I'm the source node after migration")
                entity.state = State.CONFIGURED
                self.currentEntities.update({entity_uuid: entity})
                self.cleanEntity(entity_uuid)
                self.undefineEntity(entity_uuid)


    def reactToCache(self, uri, value, v):
        print("KVM on React \nURI:%s\nValue:%s\nVersion:%s" % (uri, value, v))
        uuid = uri.split('/')[-1]
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
                if action == 'landing':
                    react_func(entity_data, dst=True)

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

    def wait_boot(self, filename):
        time.sleep(5)
        boot_regex = r"\[.+?\].+\[.+?\]:.+Cloud-init.+?v..+running.+'modules:final'.+Up.([0-9]*\.?[0-9]+).+seconds.\n"
        while True:
            file = open(filename, 'r')
            import os
            # Find the size of the file and move to the end
            st_results = os.stat(filename)
            st_size = st_results[6]
            file.seek(st_size)

            while 1:
                where = file.tell()
                line = file.readline()
                if not line:
                    time.sleep(1)
                    file.seek(where)
                else:
                    m = re.search(boot_regex, str(line))
                    if m:
                        found = m.group(1)
                        return found

    def react(self, action):
        r = {
            'define': self.defineEntity,
            'configure': self.configureEntity,
            'clean': self.cleanEntity,
            'undefine': self.undefineEntity,
            'stop': self.stopEntity,
            'resume': self.resumeEntity,
            'run': self.runEntity,
            'landing': self.migrateEntity,
            'taking_off': self.migrateEntity
        }

        return r.get(action, None)
