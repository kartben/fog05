import sys
import os
import uuid
sys.path.append(os.path.join(sys.path[0],'interfaces'))
from fog05.interfaces.States import State
from fog05.interfaces.RuntimePlugin import *
from KVMLibvirtEntity import KVMLibvirtEntity
from jinja2 import Environment
import json
import random
import time
import re
import libvirt

class KVMLibvirt(RuntimePlugin):

    def __init__(self, name, version, agent):
        super(KVMLibvirt, self).__init__(version)
        self.uuid = uuid.uuid4()
        self.name = name
        self.agent = agent
        self.agent.logger.info('__init__()', ' Hello from KVM Plugin')
        self.BASE_DIR = "/opt/fos"
        self.DISK_DIR = "disks"
        self.IMAGE_DIR = "images"
        self.LOG_DIR = "logs"
        self.HOME = str("runtime/%s/entity" % self.uuid)
        self.startRuntime()
        self.conn = None


    def startRuntime(self):
        self.agent.logger.info('startRuntime()', ' KVM Plugin - Connecting to KVM')
        self.conn = libvirt.open("qemu:///system")
        self.agent.logger.info('startRuntime()', '[ DONE ] KVM Plugin - Connecting to KVM')
        uri = str('%s/%s/*' % (self.agent.dhome, self.HOME))
        self.agent.logger.info('startRuntime()',' KVM Plugin - Observing %s' % uri)
        self.agent.dstore.observe(uri, self.__react_to_cache)

        '''check if dirs exists if not exists create'''
        if self.agent.getOSPlugin().dirExists(self.BASE_DIR):
            if not self.agent.getOSPlugin().dirExists(str("%s/%s") % (self.BASE_DIR, self.DISK_DIR)):
                self.agent.getOSPlugin().createDir(str("%s/%s") % (self.BASE_DIR, self.DISK_DIR))
            if not self.agent.getOSPlugin().dirExists(str("%s/%s") % (self.BASE_DIR, self.IMAGE_DIR)):
                self.agent.getOSPlugin().createDir(str("%s/%s") % (self.BASE_DIR, self.IMAGE_DIR))
            if not self.agent.getOSPlugin().dirExists(str("%s/%s") % (self.BASE_DIR, self.LOG_DIR)):
                self.agent.getOSPlugin().createDir(str("%s/%s") % (self.BASE_DIR, self.LOG_DIR))
        else:
            self.agent.getOSPlugin().createDir(str("%s") % self.BASE_DIR)
            self.agent.getOSPlugin().createDir(str("%s/%s") % (self.BASE_DIR, self.DISK_DIR))
            self.agent.getOSPlugin().createDir(str("%s/%s") % (self.BASE_DIR, self.IMAGE_DIR))
            self.agent.getOSPlugin().createDir(str("%s/%s") % (self.BASE_DIR, self.LOG_DIR))


        return self.uuid

    def stopRuntime(self):
        self.agent.logger.info('stopRuntime()', ' KVM Plugin - Destroying running domains')
        for k in list(self.current_entities.keys()):
            self.stopEntity(k)
            self.cleanEntity(k)
            self.undefineEntity(k)

        self.conn.close()
        self.agent.logger.info('stopRuntime()', '[ DONE ] KVM Plugin - Bye Bye')

    def getEntities(self):
        return self.current_entities

    def defineEntity(self, *args, **kwargs):
        """
        Try defining vm
        generating xml from templates/vm.xml with jinja2
        """
        self.agent.logger.info('defineEntity()', ' KVM Plugin - Defining a VM')
        if len(args) > 0:
            entity_uuid = args[4]
            disk_path = str("%s/%s/%s.qcow2" % (self.BASE_DIR, self.DISK_DIR, entity_uuid))
            cdrom_path = str("%s/%s/%s_config.iso" % (self.BASE_DIR, self.DISK_DIR,entity_uuid))
            entity = KVMLibvirtEntity(entity_uuid, args[0], args[2], args[1], disk_path, args[3], cdrom_path, [],
                                   args[5], args[6], args[7])
        elif len(kwargs) > 0:
            entity_uuid = kwargs.get('entity_uuid')
            disk_path = str("%s/%s/%s.qcow2" % (self.BASE_DIR, self.DISK_DIR, entity_uuid))
            cdrom_path = str("%s/%s/%s_config.iso" % (self.BASE_DIR, self.DISK_DIR, entity_uuid))
            entity = KVMLibvirtEntity(entity_uuid, kwargs.get('name'), kwargs.get('cpu'), kwargs.get('memory'), disk_path,
                                      kwargs.get('disk_size'), cdrom_path, kwargs.get('networks'),
                                      kwargs.get('base_image'), kwargs.get('user-data'), kwargs.get('ssh-key'))
        else:
            return None

        entity.setState(State.DEFINED)
        self.current_entities.update({entity_uuid: entity})
        uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
        vm_info = json.loads(self.agent.dstore.get(uri))
        vm_info.update({"status": "defined"})
        self.__update_actual_store(entity_uuid, vm_info)
        self.agent.logger.info('defineEntity()', '[ DONE ] KVM Plugin - VM Defined uuid: %s' % entity_uuid)
        return entity_uuid

    def undefineEntity(self, entity_uuid):

        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('undefineEntity()', ' KVM Plugin - Undefine a VM uuid %s ' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('undefineEntity()', 'KVM Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.DEFINED:
            self.agent.logger.error('undefineEntity()', 'KVM Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state",
                                                     str("Entity %s is not in DEFINED state" % entity_uuid))
        else:
            self.current_entities.pop(entity_uuid, None)
            #self.__pop_actual_store(entity_uuid)
            self.agent.logger.info('undefineEntity()', '[ DONE ] KVM Plugin - Undefine a VM uuid %s ' % entity_uuid)
            return True

    def configureEntity(self, entity_uuid):

        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('configureEntity()', ' KVM Plugin - Configure a VM uuid %s ' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('configureEntity()', 'KVM Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.DEFINED:
            self.agent.logger.error('configureEntity()', 'KVM Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state",
                                                     str("Entity %s is not in DEFINED state" % entity_uuid))
        else:

            vm_xml = self.__generate_dom_xml(entity)
            image_name = entity.image.split('/')[-1]

            wget_cmd = str('wget %s -O %s/%s/%s' % (entity.image, self.BASE_DIR, self.IMAGE_DIR, image_name))

            conf_cmd = str("%s --hostname %s --uuid %s" % (os.path.join(sys.path[0], 'plugins', self.name,
                                                                   'templates',
                                                                 'create_config_drive.sh'), entity.name, entity_uuid))

            rm_temp_cmd = str("rm")
            if entity.user_file is not None:
                data_filename = str("userdata_%s" % entity_uuid)
                self.agent.getOSPlugin().storeFile(entity.user_file, self.BASE_DIR, data_filename)
                data_filename = str("/%s/%s" % (self.BASE_DIR, data_filename))
                conf_cmd = str(conf_cmd + " --user-data %s" % data_filename)
                #rm_temp_cmd = str(rm_temp_cmd + " %s" % data_filename)
            if entity.ssh_key is not None:
                key_filename = str("key_%s.pub" % entity_uuid)
                self.agent.getOSPlugin().storeFile(entity.ssh_key, self.BASE_DIR, key_filename)
                key_filename = str("%s/%s" % (self.BASE_DIR, key_filename))
                conf_cmd = str(conf_cmd + " --ssh-key %s" % key_filename)
                #rm_temp_cmd = str(rm_temp_cmd + " %s" % key_filename)

            conf_cmd = str(conf_cmd + " %s" % entity.cdrom)

            qemu_cmd = str("qemu-img create -f qcow2 %s %dG" % (entity.disk, entity.disk_size))

            dd_cmd = str("dd if=%s/%s/%s of=%s" % (self.BASE_DIR, self.IMAGE_DIR, image_name, entity.disk))

            entity.image = image_name

            self.agent.getOSPlugin().executeCommand(wget_cmd, True)
            self.agent.getOSPlugin().executeCommand(qemu_cmd, True)
            self.agent.getOSPlugin().executeCommand(conf_cmd, True)
            self.agent.getOSPlugin().executeCommand(dd_cmd, True)

            if entity.ssh_key is not None:
                self.agent.getOSPlugin().removeFile(key_filename)
            if entity.user_file is not None:
                self.agent.getOSPlugin().removeFile(data_filename)

                #self.agent.getOSPlugin().executeCommand(rm_temp_cmd)

            try:
                self.conn.defineXML(vm_xml)
            except libvirt.libvirtError as err:
                self.conn = libvirt.open("qemu:///system")
                self.conn.defineXML(vm_xml)

            entity.onConfigured(vm_xml)
            self.current_entities.update({entity_uuid: entity})

            uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
            vm_info = json.loads(self.agent.dstore.get(uri))
            vm_info.update({"status": "configured"})
            self.__update_actual_store(entity_uuid, vm_info)
            self.agent.logger.info('configureEntity()', '[ DONE ] KVM Plugin - Configure a VM uuid %s ' % entity_uuid)
            return True

    def cleanEntity(self, entity_uuid):

        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('cleanEntity()', ' KVM Plugin - Clean a VM uuid %s ' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('cleanEntity()', 'KVM Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.CONFIGURED:
            self.agent.logger.error('cleanEntity()', 'KVM Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in CONFIGURED state",
                                                     str("Entity %s is not in CONFIGURED state" % entity_uuid))
        else:
            self.__lookup_by_uuid(entity_uuid).undefine()
            #rm_cmd = str("rm -f %s %s /opt/fos/images/%s /opt/fos/logs/%s_log.log" %
            #           (entity.cdrom, entity.disk, entity.image, entity_uuid))
            #self.agent.getOSPlugin().executeCommand(rm_cmd)
            self.agent.getOSPlugin().removeFile(entity.cdrom)
            self.agent.getOSPlugin().removeFile(entity.disk)
            self.agent.getOSPlugin().removeFile(str("%s/%s/%s") % (self.BASE_DIR, self.IMAGE_DIR, entity.image))
            self.agent.getOSPlugin().removeFile(str("%s/%s/%s_log.log") % (self.BASE_DIR, self.LOG_DIR, entity_uuid))


            entity.onClean()
            self.current_entities.update({entity_uuid: entity})

            uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
            vm_info = json.loads(self.agent.dstore.get(uri))
            vm_info.update({"status": "cleaned"})
            self.__update_actual_store(entity_uuid, vm_info)
            self.agent.logger.info('cleanEntity()', '[ DONE ] KVM Plugin - Clean a VM uuid %s ' % entity_uuid)

            return True

    def runEntity(self, entity_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('runEntity()', ' KVM Plugin - Starting a VM uuid %s ' % entity_uuid)
        entity = self.current_entities.get(entity_uuid,None)
        if entity is None:
            self.agent.logger.error('runEntity()', 'KVM Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() == State.RUNNING:
            self.agent.logger.warning('runEntity()', 'KVM Plugin - Entity already running, some strange dput/put happen! eg after migration"')
        elif entity.getState() != State.CONFIGURED:
            self.agent.logger.error('runEntity()', 'KVM Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in CONFIGURED state",
                                                     str("Entity %s is not in CONFIGURED state" % entity_uuid))
        else:
            self.__lookup_by_uuid(entity_uuid).create()
            entity.onStart()
            '''
            Then after boot should update the `actual store` with the run status of the vm  
            '''
            log_filename = str("%s/%s/%s_log.log" % (self.BASE_DIR,self.LOG_DIR, entity_uuid))
            if entity.user_file is not None:
                self.__wait_boot(log_filename, True)
            else:
                self.__wait_boot(log_filename)

            self.agent.logger.info('runEntity()', ' KVM Plugin - VM %s Started!' % entity_uuid)
            uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
            vm_info = json.loads(self.agent.dstore.get(uri))
            vm_info.update({"status": "run"})
            self.__update_actual_store(entity_uuid, vm_info)
            '''
            vm_info = .... load vm info from desidered store, update and save to actual store
            json_data = json.dumps(vm_info)
            uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s' % (self.agent.uuid, self.uuid, entity_uuid))
            self.agent.store.put(uri, json_data)
            
            '''
            self.current_entities.update({entity_uuid: entity})
            self.agent.logger.info('runEntity()', '[ DONE ] KVM Plugin - Starting a VM uuid %s ' % entity_uuid)
            return True

    def stopEntity(self, entity_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('stopEntity()', ' KVM Plugin - Stop a VM uuid %s ' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('stopEntity()', 'KVM Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.RUNNING:
            self.agent.logger.error('stopEntity()', 'KVM Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in RUNNING state",
                                                     str("Entity %s is not in RUNNING state" % entity_uuid))
        else:
            self.__lookup_by_uuid(entity_uuid).destroy()
            entity.onStop()
            self.current_entities.update({entity_uuid: entity})

            uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
            vm_info = json.loads(self.agent.dstore.get(uri))
            vm_info.update({"status": "stop"})
            self.__update_actual_store(entity_uuid, vm_info)
            self.agent.logger.info('stopEntity()', '[ DONE ] KVM Plugin - Stop a VM uuid %s ' % entity_uuid)

            return True

    def pauseEntity(self, entity_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('pauseEntity()', ' KVM Plugin - Pause a VM uuid %s ' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('pauseEntity()', 'KVM Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.RUNNING:
            self.agent.logger.error('pauseEntity()', 'KVM Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in RUNNING state",
                                                     str("Entity %s is not in RUNNING state" % entity_uuid))
        else:
            self.__lookup_by_uuid(entity_uuid).suspend()
            entity.onPause()
            self.current_entities.update({entity_uuid: entity})
            uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
            vm_info = json.loads(self.agent.dstore.get(uri))
            vm_info.update({"status": "pause"})
            self.__update_actual_store(entity_uuid, vm_info)
            self.agent.logger.info('pauseEntity()', '[ DONE ] KVM Plugin - Pause a VM uuid %s ' % entity_uuid)
            return True

    def resumeEntity(self, entity_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('resumeEntity()', ' KVM Plugin - Resume a VM uuid %s ' % entity_uuid)
        entity = self.current_entities.get(entity_uuid,None)
        if entity is None:
            self.agent.logger.error('resumeEntity()', 'KVM Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.PAUSED:
            self.agent.logger.error('resumeEntity()', 'KVM Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in PAUSED state",
                                                     str("Entity %s is not in PAUSED state" % entity_uuid))
        else:
            self.__lookup_by_uuid(entity_uuid).resume()
            entity.onResume()
            self.current_entities.update({entity_uuid: entity})

            uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
            vm_info = json.loads(self.agent.dstore.get(uri))
            vm_info.update({"status": "run"})
            self.__update_actual_store(entity_uuid, vm_info)
            self.agent.logger.info('resumeEntity()', '[ DONE ] KVM Plugin - Resume a VM uuid %s ' % entity_uuid)
            return True


    def migrateEntity(self, entity_uuid,  dst=False):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('migrateEntity()', ' KVM Plugin - Migrate a VM uuid %s ' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            if dst is True:
                self.agent.logger.info('migrateEntity()', " KVM Plugin - I\'m the Destination Node")
                self.beforeMigrateEntityActions(entity_uuid, True)

                while True:  # wait for migration to be finished
                    dom = self.__lookup_by_uuid(entity_uuid)
                    if dom is None:
                        self.agent.logger.info('migrateEntity()', ' KVM Plugin - Domain not already in this host')
                        time.sleep(10)
                    else:
                        if dom.isActive() == 1:
                            break
                        else:
                            self.agent.logger.info('migrateEntity()', ' KVM Plugin - Domain in this host but not running')
                            time.sleep(10)

                self.afterMigrateEntityActions(entity_uuid, True)
                self.agent.logger.info('migrateEntity()', '[ DONE ] KVM Plugin - Migrate a VM uuid %s ' % entity_uuid)
                return True

            else:
                self.agent.logger.error('migrateEntity()', 'KVM Plugin - Entity not exists')
                raise EntityNotExistingException("Enitity not existing",
                                                 str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.RUNNING:
            self.agent.logger.error('migrateEntity()', 'KVM Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in RUNNING state",
                                                     str("Entity %s is not in RUNNING state" % entity_uuid))
        else:
            self.agent.logger.info('migrateEntity()', " KVM Plugin - I\'m the Source Node")
            self.beforeMigrateEntityActions(entity_uuid)
            self.afterMigrateEntityActions(entity_uuid)


    def beforeMigrateEntityActions(self, entity_uuid, dst=False):
        if dst is True:
            self.agent.logger.info('beforeMigrateEntityActions()', ' KVM Plugin - Before Migration Destination: Create Domain and destination files')
            uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
            entity_info = json.loads(self.agent.dstore.get(uri))
            vm_info = entity_info.get("entity_data")
            disk_path = str("%s/%s/%s.qcow2" % (self.BASE_DIR, self.DISK_DIR, entity_uuid))
            cdrom_path = str("%s/%s/%s_config.iso" % (self.BASE_DIR, self.DISK_DIR, entity_uuid))
            entity = KVMLibvirtEntity(entity_uuid, vm_info.get('name'), vm_info.get('cpu'), vm_info.get('memory'),
                                      disk_path,
                                      vm_info.get('disk_size'), cdrom_path, vm_info.get('networks'),
                                      vm_info.get('base_image'), vm_info.get('user-data'), vm_info.get('ssh-key'))

            entity.state = State.LANDING
            qemu_cmd = str("qemu-img create -f qcow2 %s %dG" % (entity.disk, entity.disk_size))
            vm_xml = self.__generate_dom_xml(entity)

            try:
                self.conn.defineXML(vm_xml)
            except libvirt.libvirtError as err:
                self.conn = libvirt.open("qemu:///system")
                self.conn.defineXML(vm_xml)
            self.agent.getOSPlugin().executeCommand(qemu_cmd)
            self.agent.getOSPlugin().createFile(entity.cdrom)
            self.current_entities.update({entity_uuid: entity})

            entity_info.update({"status": "landing"})
            self.__update_actual_store(entity_uuid, vm_info)

            return True
        else:
            self.agent.logger.info('beforeMigrateEntityActions()', ' KVM Plugin - Before Migration Source: get information about destination node')
            entity = self.current_entities.get(entity_uuid, None)
            uri = str("%s/%s/%s" % (self.agent.dhome, self.HOME, entity_uuid))
            fognode_uuid = json.loads(self.agent.dstore.get(uri)).get("dst")

            uri = str('afos://<sys-id>/%s/plugins' % fognode_uuid)
            all_plugins = json.loads(self.agent.astore.get(uri)).get('plugins')

            runtimes = [x for x in all_plugins if x.get('type') == 'runtime']
            search = [x for x in runtimes if 'KVMLibvirt' in x.get('name')]
            if len(search) == 0:
                self.agent.logger.error('beforeMigrateEntityActions()', 'KVM Plugin - Before Migration Source: No KVM Plugin, Aborting!!!')
                exit()
            else:
                kvm = search[0]



            flag = False
            while flag:
                self.agent.logger.info('beforeMigrateEntityActions()', ' KVM Plugin - Before Migration Source: Waiting destination to be '
                                        'ready')
                time.sleep(1)
                uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (dst, kvm.get('uuid'), entity_uuid))
                vm_info = json.loads(self.agent.astore.get(uri))
                if vm_info is not None:
                    if vm_info.get("status") == "landing":
                        flag = True

            entity.state = State.TAKING_OFF
            self.current_entities.update({entity_uuid: entity})
            uri = str("afos://<sys-id>/%s/" % fognode_uuid)
            dst_node_info = json.loads(self.agent.astore.get(uri))

            dom = self.__lookup_by_uuid(entity_uuid)
            nw = dst_node_info.get('network')

            dst_hostname = dst_node_info.get('name')

            dst_ip = [x for x in nw if x.get("inft_configuration").get("ipv4_gateway") != ""]
            # TODO: or x.get("inft_configuration").get("ipv6_gateway") for ip_v6
            if len(dst_ip) == 0:
                return False

            dst_ip = dst_ip[0].get("inft_configuration").get("ipv4_address") # TODO: as on search should use ipv6

            # ## ADDING TO /etc/hosts otherwise migration can fail
            self.agent.getOSPlugin().addKnowHost(dst_hostname, dst_ip)
            ###

            # ## ACTUAL MIGRATIION ##################
            dst_host = str('qemu+ssh://%s/system' % dst_ip)
            dest_conn = libvirt.open(dst_host)
            if dest_conn is None:
                self.agent.logger.error('beforeMigrateEntityActions()', 'KVM Plugin - Before Migration Source: Error on libvirt connection')
                exit(1)
            new_dom = dom.migrate(dest_conn, libvirt.VIR_MIGRATE_LIVE, entity.name, None, 0)
            if new_dom is None:
                self.agent.logger.error('beforeMigrateEntityActions()', 'KVM Plugin - Before Migration Source: Migration failed')
                exit(1)

                self.agent.logger.info('beforeMigrateEntityActions()', ' KVM Plugin - Before Migration Source: Migration succeeds')
            dest_conn.close()
            # #######################################

            # ## REMOVING AFTER MIGRATION
            self.agent.getOSPlugin().removeKnowHost(dst_hostname)

            return True

    def afterMigrateEntityActions(self, entity_uuid, dst=False):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('afterMigrateEntityActions()', 'KVM Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() not in (State.TAKING_OFF, State.LANDING, State.RUNNING):
            self.agent.logger.error('afterMigrateEntityActions()', 'KVM Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in correct state",
                                                     str("Entity %s is not in correct state" % entity.getState()))
        else:
            if dst is True:
                '''
                Here the plugin also update to the current status, and remove unused keys
                '''
                self.agent.logger.info('afterMigrateEntityActions()', ' KVM Plugin - After Migration Destination: Updating state')
                entity.state = State.RUNNING
                self.current_entities.update({entity_uuid: entity})

                uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
                vm_info = json.loads(self.agent.dstore.get(uri))
                vm_info.pop('dst')
                vm_info.update({"status": "run"})
                self.__update_actual_store(entity_uuid, vm_info)

                return True
            else:
                '''
                Source node destroys all information about vm
                '''
                self.agent.logger.info('afterMigrateEntityActions()', ' KVM Plugin - After Migration Source: Updating state, destroy vm')
                entity.state = State.CONFIGURED
                self.current_entities.update({entity_uuid: entity})
                self.cleanEntity(entity_uuid)
                self.undefineEntity(entity_uuid)
                return True

    def __react_to_cache(self, uri, value, v):
        self.agent.logger.info('__react_to_cache()', ' KVM Plugin - React to to URI: %s Value: %s Version: %s' % (uri, value, v))
        if value is None and v is None:
            self.agent.logger.info('__react_to_cache()', ' KVM Plugin - This is a remove for URI: %s' % uri)
        else:
            uuid = uri.split('/')[-1]
            value = json.loads(value)
            action = value.get('status')
            entity_data = value.get('entity_data')
            react_func = self.__react(action)
            if react_func is not None and entity_data is None:
                react_func(uuid)
            elif react_func is not None:
                entity_data.update({'entity_uuid': uuid})
                if action == 'define':
                    react_func(**entity_data)
                else:
                    if action == 'landing':
                        react_func(entity_data, dst=True)
                    else:
                        react_func(entity_data)

    def __random_mac_generator(self):
        mac = [0x00, 0x16, 0x3e,
               random.randint(0x00, 0x7f),
               random.randint(0x00, 0xff),
               random.randint(0x00, 0xff)]
        return ':'.join(map(lambda x: "%02x" % x, mac))

    def __lookup_by_uuid(self, uuid):
        try:
            domains = self.conn.listAllDomains(0)
        except libvirt.libvirtError as err:
            self.conn = libvirt.open("qemu:///system")
            domains = self.conn.listAllDomains(0)

        if len(domains) != 0:
            for domain in domains:
                if str(uuid) == domain.UUIDString():
                    return domain
        else:
            return None

    def __wait_boot(self, filename, configured=False):
        time.sleep(5)
        if configured:
            boot_regex = r"\[.+?\].+\[.+?\]:.+Cloud-init.+?v..+running.+'modules:final'.+Up.([0-9]*\.?[0-9]+).+seconds.\n"
        else:
            boot_regex = r".+?login:()"
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

    def __generate_dom_xml(self, entity):
        template_xml = self.agent.getOSPlugin().readFile(os.path.join(sys.path[0], 'plugins', self.name,
                                                                      'templates', 'vm.xml'))
        vm_xml = Environment().from_string(template_xml)
        vm_xml = vm_xml.render(name=entity.name, uuid=entity.uuid, memory=entity.ram,
                               cpu=entity.cpu, disk_image=entity.disk,
                               iso_image=entity.cdrom, networks=entity.networks)
        return vm_xml

    def __update_actual_store(self, uri, value):
        uri = str("%s/%s/%s" % (self.agent.ahome, self.HOME, uri))
        value = json.dumps(value)
        self.agent.astore.put(uri, value)

    def __pop_actual_store(self, uri,):
        uri = str("%s/%s/%s" % (self.agent.ahome, self.HOME, uri))
        self.agent.astore.remove(uri)



    def __react(self, action):
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
