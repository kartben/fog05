import sys
import os
import uuid
from fog05.interfaces.States import State
from fog05.interfaces.RuntimePlugin import *
from KVMLibvirtEntity import KVMLibvirtEntity
from KVMLibvirtEntityInstance import KVMLibvirtEntityInstance
from jinja2 import Environment
import json
import random
import time
import re
import libvirt
import ipaddress

class KVMLibvirt(RuntimePlugin):

    def __init__(self, name, version, agent, plugin_uuid):
        super(KVMLibvirt, self).__init__(version, plugin_uuid)
        self.name = name
        self.agent = agent
        self.agent.logger.info('__init__()', ' Hello from KVM Plugin')
        self.BASE_DIR = os.path.join(self.agent.base_path, 'kvm')
        #self.BASE_DIR = "/opt/fos/kvm"
        self.DISK_DIR = "disks"
        self.IMAGE_DIR = "images"
        self.LOG_DIR = "logs"
        self.HOME = str("runtime/%s/entity" % self.uuid)
        self.INSTANCE = "instance"
        file_dir = os.path.dirname(__file__)
        self.DIR = os.path.abspath(file_dir)
        self.conn = None
        self.start_runtime()



    def start_runtime(self):
        self.agent.logger.info('startRuntime()', ' KVM Plugin - Connecting to KVM')
        self.conn = libvirt.open("qemu:///system")
        self.agent.logger.info('startRuntime()', '[ DONE ] KVM Plugin - Connecting to KVM')
        uri = str('%s/%s/*' % (self.agent.dhome, self.HOME))
        self.agent.logger.info('startRuntime()',' KVM Plugin - Observing %s' % uri)
        self.agent.dstore.observe(uri, self.__react_to_cache)

        '''check if dirs exists if not exists create'''
        if self.agent.get_os_plugin().dir_exists(self.BASE_DIR):
            if not self.agent.get_os_plugin().dir_exists(os.path.join(self.BASE_DIR, self.DISK_DIR)):
                self.agent.get_os_plugin().create_dir(os.path.join(self.BASE_DIR, self.DISK_DIR))
            if not self.agent.get_os_plugin().dir_exists(os.path.join(self.BASE_DIR, self.IMAGE_DIR)):
                self.agent.get_os_plugin().create_dir(os.path.join(self.BASE_DIR, self.IMAGE_DIR))
            if not self.agent.get_os_plugin().dir_exists(os.path.join(self.BASE_DIR, self.LOG_DIR)):
                self.agent.get_os_plugin().create_dir(os.path.join(self.BASE_DIR, self.LOG_DIR))
        else:
            self.agent.get_os_plugin().create_dir(str("%s") % self.BASE_DIR)
            self.agent.get_os_plugin().create_dir(os.path.join(self.BASE_DIR, self.DISK_DIR))
            self.agent.get_os_plugin().create_dir(os.path.join(self.BASE_DIR, self.IMAGE_DIR))
            self.agent.get_os_plugin().create_dir(os.path.join(self.BASE_DIR, self.LOG_DIR))


        return self.uuid

    def stop_runtime(self):
        self.agent.logger.info('stopRuntime()', ' KVM Plugin - Destroying running domains')
        for k in list(self.current_entities.keys()):
            entity = self.current_entities.get(k)
            for i in list(entity.instances.keys()):
                self.__force_entity_instance_termination(k, i)
            # if entity.get_state() == State.PAUSED:
            #     self.resume_entity(k)
            #     self.stop_entity(k)
            #     self.clean_entity(k)
            #     self.undefine_entity(k)
            # if entity.get_state() == State.RUNNING:
            #     self.stop_entity(k)
            #     self.clean_entity(k)
            #     self.undefine_entity(k)
            # if entity.get_state() == State.CONFIGURED:
            #     self.clean_entity(k)
            #     self.undefine_entity(k)
            if entity.get_state() == State.DEFINED:
                self.undefine_entity(k)

        self.conn.close()
        self.agent.logger.info('stopRuntime()', '[ DONE ] KVM Plugin - Bye Bye')

    def get_entities(self):
        return self.current_entities

    def define_entity(self, *args, **kwargs):
        """
        Try defining vm
        generating xml from templates/vm.xml with jinja2


        the base image should donwloaded now!!

        """
        self.agent.logger.info('define_entity()', ' KVM Plugin - Defining a VM')

        if len(args) > 0:
            entity_uuid = args[4]
            disk_path = str('%s.qcow2' % entity_uuid)
            cdrom_path = str('%s_config.iso' % entity_uuid)
            disk_path = os.path.join(self.BASE_DIR, self.DISK_DIR, disk_path)
            cdrom_path = os.path.join(self.BASE_DIR, self.DISK_DIR, cdrom_path)
            entity = KVMLibvirtEntity(entity_uuid, args[0], args[2], args[1], disk_path, args[3], cdrom_path, [],
                                   args[5], args[6], args[7])
        elif len(kwargs) > 0:
            entity_uuid = kwargs.get('entity_uuid')
            disk_path = str('%s.qcow2' % entity_uuid)
            cdrom_path = str('%s_config.iso' % entity_uuid)
            disk_path = os.path.join(self.BASE_DIR, self.DISK_DIR, disk_path)
            cdrom_path = os.path.join(self.BASE_DIR, self.DISK_DIR, cdrom_path)
            entity = KVMLibvirtEntity(entity_uuid, kwargs.get('name'), kwargs.get('cpu'), kwargs.get('memory'), disk_path,
                                      kwargs.get('disk_size'), cdrom_path, kwargs.get('networks'),
                                      kwargs.get('base_image'), kwargs.get('user-data'), kwargs.get('ssh-key'))
        else:
            return None

        image_name = os.path.join(self.BASE_DIR, self.IMAGE_DIR, entity.image_url.split('/')[-1])
        self.agent.get_os_plugin().download_file(entity.image_url, image_name)
        entity.image = image_name

        entity.set_state(State.DEFINED)
        self.current_entities.update({entity_uuid: entity})
        uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
        vm_info = json.loads(self.agent.dstore.get(uri))
        vm_info.update({"status": "defined"})
        self.__update_actual_store(entity_uuid, vm_info)
        self.agent.logger.info('define_entity()', '[ DONE ] KVM Plugin - VM Defined uuid: %s' % entity_uuid)
        return entity_uuid

    def undefine_entity(self, entity_uuid):

        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('undefine_entity()', ' KVM Plugin - Undefine a VM uuid %s ' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('undefine_entity()', 'KVM Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('undefine_entity()', 'KVM Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state",
                                                     str("Entity %s is not in DEFINED state" % entity_uuid))
        else:
            if(self.current_entities.pop(entity_uuid, None)) is None:
                self.agent.logger.warning('undefine_entity()', 'KVM Plugin - pop from entities dict returned none')

            for i in list(entity.instances.keys()):
                self.__force_entity_instance_termination(entity_uuid, i)
            self.agent.get_os_plugin().remove_file(os.path.join(self.BASE_DIR, self.IMAGE_DIR, entity.image))
            self.__pop_actual_store(entity_uuid)
            self.agent.logger.info('undefine_entity()', '[ DONE ] KVM Plugin - Undefine a VM uuid %s ' % entity_uuid)
            return True

    def configure_entity(self, entity_uuid, instance_uuid=None):
        '''
        :param entity_uuid:
        :param instance_uuid:
        :return:
        '''

        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('configure_entity()', ' KVM Plugin - Configure a VM uuid %s ' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('configure_entity()', 'KVM Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('configure_entity()', 'KVM Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state",
                                                     str("Entity %s is not in DEFINED state" % entity_uuid))
        else:

            if instance_uuid is None:
                instance_uuid = str(uuid.uuid4())

            if entity.has_instance(instance_uuid):
                print("This instance already existis!!")
            else:

                id = len(entity.instances)
                name = '{0}{1}'.format(entity.name, id)
                disk_path = str('%s.qcow2' % instance_uuid)
                cdrom_path = str('%s_config.iso' % instance_uuid)
                disk_path = os.path.join(self.BASE_DIR, self.DISK_DIR, disk_path)
                cdrom_path = os.path.join(self.BASE_DIR, self.DISK_DIR, cdrom_path)
                #uuid, name, cpu, ram, disk, disk_size, cdrom, networks, image, user_file, ssh_key, entity_uuid)
                instance = KVMLibvirtEntityInstance(instance_uuid, name, entity.cpu, entity.ram, disk_path,
                                      entity.disk_size, cdrom_path, entity.networks, entity.image, entity.user_file,
                                      entity.ssh_key, entity_uuid)
                for i, n in enumerate(instance.networks):
                    if n.get('type') in ['wifi']:

                        nw_ifaces =  self.agent.get_os_plugin().get_network_informations()
                        for iface in nw_ifaces:
                            if self.agent.get_os_plugin().get_intf_type(iface.get('intf_name')) == 'wireless' and iface.get('available') is True:
                                self.agent.get_os_plugin().set_interface_unaviable(iface.get('intf_name'))
                                n.update({'direct_intf': iface.get('intf_name')})
                        # TODO get available interface from os plugin
                    if n.get('network_uuid') is not None:
                        nws = self.agent.get_network_plugin(None).get(list(self.agent.get_network_plugin(None).keys())[0])
                        #print(nws.getNetworkInfo(n.get('network_uuid')))
                        br_name = nws.get_network_info(n.get('network_uuid')).get('virtual_device')
                        #print(br_name)
                        n.update({'br_name': br_name})
                    if n.get('intf_name') is None:
                        n.update({'intf_name': 'veth{0}'.format(i)})

                vm_xml = self.__generate_dom_xml(instance)
                #image_name = instance.image.split('/')[-1]

                #wget_cmd = str('wget %s -O %s/%s/%s' % (entity.image, self.BASE_DIR, self.IMAGE_DIR, image_name))
                #image_url = instance.image

                conf_cmd = str("%s --hostname %s --uuid %s" % (os.path.join(self.DIR, 'templates',
                                                                     'create_config_drive.sh'), entity.name, entity_uuid))

                rm_temp_cmd = str("rm")
                if instance.user_file is not None and instance.user_file != '':
                    data_filename = str("userdata_%s" % entity_uuid)
                    self.agent.get_os_plugin().store_file(entity.user_file, self.BASE_DIR, data_filename)
                    data_filename = os.path.join(self.BASE_DIR, data_filename)
                    conf_cmd = str(conf_cmd + " --user-data %s" % data_filename)
                    #rm_temp_cmd = str(rm_temp_cmd + " %s" % data_filename)
                if instance.ssh_key is not None and instance.ssh_key != '':
                    key_filename = str("key_%s.pub" % entity_uuid)
                    self.agent.get_os_plugin().store_file(instance.ssh_key, self.BASE_DIR, key_filename)
                    key_filename = os.path.join(self.BASE_DIR, key_filename)
                    conf_cmd = str(conf_cmd + " --ssh-key %s" % key_filename)
                    #rm_temp_cmd = str(rm_temp_cmd + " %s" % key_filename)

                conf_cmd = str(conf_cmd + " %s" % instance.cdrom)

                qemu_cmd = str("qemu-img create -f qcow2 %s %dG" % (instance.disk, instance.disk_size))

                dd_cmd = str("dd if=%s of=%s" % (instance.image, instance.disk))

                #instance.image = image_name

                #self.agent.getOSPlugin().executeCommand(wget_cmd, True)
                #self.agent.getOSPlugin().downloadFile(image_url, os.path.join(self.BASE_DIR, self.IMAGE_DIR, image_name))
                self.agent.get_os_plugin().execute_command(qemu_cmd, True)
                self.agent.get_os_plugin().execute_command(conf_cmd, True)
                self.agent.get_os_plugin().execute_command(dd_cmd, True)

                if instance.ssh_key is not None and instance.ssh_key != '':
                    self.agent.get_os_plugin().remove_file(key_filename)
                if instance.user_file is not None and instance.user_file != '':
                    self.agent.get_os_plugin().remove_file(data_filename)

                    #self.agent.getOSPlugin().executeCommand(rm_temp_cmd)

                try:
                    self.conn.defineXML(vm_xml)
                except libvirt.libvirtError as err:
                    self.conn = libvirt.open("qemu:///system")
                    self.conn.defineXML(vm_xml)

                instance.on_configured(vm_xml)
                entity.add_instance(instance)
                self.current_entities.update({entity_uuid: entity})

                uri = str('%s/%s/%s' % (self.agent.ahome, self.HOME, entity_uuid))
                vm_info = json.loads(self.agent.astore.get(uri))
                vm_info.update({"status": "configured"})
                vm_info.update({"name": instance.name})

                self.__update_actual_store_instance(entity_uuid,instance_uuid, vm_info)
                #self.__update_actual_store(entity_uuid, vm_info)

                self.agent.logger.info('configure_entity()', '[ DONE ] KVM Plugin - Configure a VM uuid %s ' % entity_uuid)
                return True

    def clean_entity(self, entity_uuid, instance_uuid=None):

        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('clean_entity()', ' KVM Plugin - Clean a VM uuid %s ' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('clean_entity()', 'KVM Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('clean_entity()', 'KVM Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state",
                                                     str("Entity %s is not in DEFINED state" % entity_uuid))
        else:

            if instance_uuid is None or not entity.has_instance(instance_uuid):
                self.agent.logger.error('clean_entity()','KVM Plugin - Instance not found!!')
            else:
                instance = entity.get_instance(instance_uuid)
                if instance.get_state() != State.CONFIGURED:
                    self.agent.logger.error('clean_entity()',
                                        'KVM Plugin - Instance state is wrong, or transition not allowed')
                    raise StateTransitionNotAllowedException("Instance is not in CONFIGURED state",
                                                         str("Instance %s is not in CONFIGURED state" % instance_uuid))
                else:
                    dom = self.__lookup_by_uuid(instance_uuid)
                    if dom is not None:
                        dom.undefine()
                    else:
                        self.agent.logger.error('clean_entity()', 'KVM Plugin - Domain not found!!')
                    #rm_cmd = str("rm -f %s %s /opt/fos/images/%s /opt/fos/logs/%s_log.log" %
                    #           (entity.cdrom, entity.disk, entity.image, entity_uuid))
                    #self.agent.getOSPlugin().executeCommand(rm_cmd)
                    self.agent.get_os_plugin().remove_file(instance.cdrom)
                    self.agent.get_os_plugin().remove_file(instance.disk)
                    #self.agent.getOSPlugin().removeFile(os.path.join(self.BASE_DIR, self.IMAGE_DIR, instance.image))
                    self.agent.get_os_plugin().remove_file(os.path.join(self.BASE_DIR, self.LOG_DIR, instance_uuid))

                    entity.remove_instance(instance)
                    #entity.on_clean()
                    self.current_entities.update({entity_uuid: entity})

                    #uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
                    #vm_info = json.loads(self.agent.dstore.get(uri))
                    #vm_info.update({"status": "cleaned"})
                    #self.__update_actual_store(entity_uuid, vm_info)
                    self.__pop_actual_store_instance(entity_uuid, instance_uuid)
                    self.agent.logger.info('clean_entity()', '[ DONE ] KVM Plugin - Clean a VM uuid %s ' % entity_uuid)

                return True

    def run_entity(self, entity_uuid, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('run_entity()', ' KVM Plugin - Starting a VM uuid %s ' % entity_uuid)
        entity = self.current_entities.get(entity_uuid,None)
        if entity is None:
            self.agent.logger.error('run_entity()', 'KVM Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        #elif entity.get_state() == State.RUNNING:
        #    self.agent.logger.warning('run_entity()', 'KVM Plugin - Entity already running, some strange dput/put
        # happen! eg after migration"')
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('run_entity()', 'KVM Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state",
                                                     str("Entity %s is not in DEFINED state" % entity_uuid))
        else:
            if instance_uuid is None or not entity.has_instance(instance_uuid):
                self.agent.logger.error('run_entity()','KVM Plugin - Instance not found!!')
            else:
                instance = entity.get_instance(instance_uuid)
                if instance.get_state() != State.CONFIGURED:
                    self.agent.logger.error('clean_entity()',
                                            'KVM Plugin - Instance state is wrong, or transition not allowed')
                    raise StateTransitionNotAllowedException("Instance is not in CONFIGURED state",
                                                             str(
                                                                 "Instance %s is not in CONFIGURED state" % instance_uuid))
                else:
                    self.__lookup_by_uuid(instance_uuid).create()
                    instance.on_start()
                    '''
                    Then after boot should update the `actual store` with the run status of the vm  
                    '''

                    # log_filename = str("%s/%s/%s_log.log" % (self.BASE_DIR, self.LOG_DIR, instance_uuid))
                    # if instance.user_file is not None and instance.user_file != '':
                    #     self.__wait_boot(log_filename, True)
                    # else:
                    #     self.__wait_boot(log_filename)
                    #     self.__wait_boot(log_filename)

                    self.agent.logger.info('run_entity()', ' KVM Plugin - VM %s Started!' % instance)
                    uri = str('%s/%s/%s/%s/%s' % (self.agent.ahome, self.HOME, entity_uuid,self.INSTANCE,
                                                  instance_uuid))
                    vm_info = json.loads(self.agent.astore.get(uri))
                    vm_info.update({"status": "run"})
                    self.__update_actual_store_instance(entity_uuid,instance_uuid, vm_info)
                    '''
                    vm_info = .... load vm info from desidered store, update and save to actual store
                    json_data = json.dumps(vm_info)
                    uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s' % (self.agent.uuid, self.uuid, entity_uuid))
                    self.agent.store.put(uri, json_data)
                    
                    '''
                    self.current_entities.update({entity_uuid: entity})
                    self.agent.logger.info('run_entity()', '[ DONE ] KVM Plugin - Starting a VM uuid %s ' % entity_uuid)
                    return True

    def stop_entity(self, entity_uuid, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('stop_entity()', ' KVM Plugin - Stop a VM uuid %s ' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('stop_entity()', 'KVM Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('stop_entity()', 'KVM Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state",
                                                     str("Entity %s is not in DEFINED state" % entity_uuid))
        else:
            if instance_uuid is None or not entity.has_instance(instance_uuid):
                self.agent.logger.error('run_entity()', 'KVM Plugin - Instance not found!!')
            else:
                instance = entity.get_instance(instance_uuid)
                if instance.get_state() != State.RUNNING:
                    self.agent.logger.error('clean_entity()',
                                            'KVM Plugin - Instance state is wrong, or transition not allowed')
                    raise StateTransitionNotAllowedException("Instance is not in RUNNING state",
                                                             str(
                                                                 "Instance %s is not in RUNNING state" % instance_uuid))
                else:
                    self.__lookup_by_uuid(instance_uuid).destroy()
                    instance.on_stop()
                    self.current_entities.update({entity_uuid: entity})

                    uri = str('%s/%s/%s/%s/%s' % (self.agent.ahome, self.HOME, entity_uuid, self.INSTANCE, instance_uuid))
                    vm_info = json.loads(self.agent.astore.get(uri))
                    vm_info.update({"status": "stop"})
                    self.__update_actual_store_instance(entity_uuid,instance_uuid, vm_info)
                    self.agent.logger.info('stop_entity()', '[ DONE ] KVM Plugin - Stop a VM uuid %s ' % instance_uuid)

            return True

    def pause_entity(self, entity_uuid, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('pause_entity()', ' KVM Plugin - Pause a VM uuid %s ' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('pause_entity()', 'KVM Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('pause_entity()', 'KVM Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state",
                                                     str("Entity %s is not in DEFINED state" % entity_uuid))
        else:
            if instance_uuid is None or not entity.has_instance(instance_uuid):
                self.agent.logger.error('run_entity()', 'KVM Plugin - Instance not found!!')
            else:
                instance = entity.get_instance(instance_uuid)
                if instance.get_state() != State.RUNNING:
                    self.agent.logger.error('clean_entity()',
                                            'KVM Plugin - Instance state is wrong, or transition not allowed')
                    raise StateTransitionNotAllowedException("Instance is not in RUNNING state",
                                                             str(
                                                                 "Instance %s is not in RUNNING state" % instance_uuid))
                else:
                    self.__lookup_by_uuid(instance_uuid).suspend()
                    instance.on_pause()
                    self.current_entities.update({entity_uuid: entity})
                    uri = str(
                        '%s/%s/%s/%s/%s' % (self.agent.ahome, self.HOME, entity_uuid, self.INSTANCE, instance_uuid))
                    vm_info = json.loads(self.agent.astore.get(uri))
                    vm_info.update({"status": "pause"})
                    self.__update_actual_store_instance(entity_uuid,instance_uuid, vm_info)
                    self.agent.logger.info('pause_entity()', '[ DONE ] KVM Plugin - Pause a VM uuid %s ' % instance_uuid)
                    return True

    def resume_entity(self, entity_uuid, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('resume_entity()', ' KVM Plugin - Resume a VM uuid %s ' % entity_uuid)
        entity = self.current_entities.get(entity_uuid,None)
        if entity is None:
            self.agent.logger.error('resume_entity()', 'KVM Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('resume_entity()', 'KVM Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state",
                                                     str("Entity %s is not in DEFINED state" % entity_uuid))
        else:
            if instance_uuid is None or not entity.has_instance(instance_uuid):
                self.agent.logger.error('run_entity()', 'KVM Plugin - Instance not found!!')
            else:
                instance = entity.get_instance(instance_uuid)
                if instance.get_state() != State.PAUSED:
                    self.agent.logger.error('clean_entity()',
                                            'KVM Plugin - Instance state is wrong, or transition not allowed')
                    raise StateTransitionNotAllowedException("Instance is not in PAUSED state",
                                                             str(
                                                                 "Instance %s is not in PAUSED state" % entity_uuid))
                else:
                    self.__lookup_by_uuid(instance_uuid).resume()
                    instance_uuid.on_resume()
                    self.current_entities.update({entity_uuid: entity})
                    uri = str(
                        '%s/%s/%s/%s/%s' % (self.agent.ahome, self.HOME, entity_uuid, self.INSTANCE, instance_uuid))
                    vm_info = json.loads(self.agent.dstore.get(uri))
                    vm_info.update({"status": "run"})
                    self.__update_actual_store_instance(entity_uuid,instance_uuid, vm_info)
                    self.agent.logger.info('resume_entity()', '[ DONE ] KVM Plugin - Resume a VM uuid %s ' % instance_uuid)
                    return True


    def migrate_entity(self, entity_uuid, dst=False, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('migrate_entity()', ' KVM Plugin - Migrate a VM uuid %s ' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            if dst is True:

                self.agent.logger.info('migrate_entity()', " KVM Plugin - I\'m the Destination Node")
                self.before_migrate_entity_actions(entity_uuid, True, instance_uuid)

                while True:  # wait for migration to be finished
                    dom = self.__lookup_by_uuid(instance_uuid)
                    if dom is None:
                        self.agent.logger.info('migrate_entity()', ' KVM Plugin - Domain not already in this host')
                        time.sleep(5)
                    else:
                        if dom.isActive() == 1:
                            break
                        else:
                            self.agent.logger.info('migrate_entity()', ' KVM Plugin - Domain in this host but not running')
                            time.sleep(5)


                self.after_migrate_entity_actions(entity_uuid, True, instance_uuid)
                self.agent.logger.info('migrate_entity()', '[ DONE ] KVM Plugin - Migrate a VM uuid %s ' % entity_uuid)
                return True

            else:
                self.agent.logger.error('migrate_entity()', 'KVM Plugin - Entity not exists')
                raise EntityNotExistingException("Enitity not existing",
                                                 str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('migrate_entity()', 'KVM Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state",
                                                     str("Entity %s is not in DEFINED state" % entity_uuid))
        else:
            instance = entity.get_instance(instance_uuid)
            if instance.get_state() not in [State.RUNNING, State.TAKING_OFF]:
                self.agent.logger.error('clean_entity()',
                                        'KVM Plugin - Instance state is wrong, or transition not allowed')
                raise StateTransitionNotAllowedException("Instance is not in RUNNING state",
                                                         str(
                                                             "Instance %s is not in RUNNING state" % entity_uuid))
            self.agent.logger.info('migrate_entity()', " KVM Plugin - I\'m the Source Node")
            self.before_migrate_entity_actions(entity_uuid, instance_uuid=instance_uuid)
            self.after_migrate_entity_actions(entity_uuid,  instance_uuid=instance_uuid)


    def before_migrate_entity_actions(self, entity_uuid, dst=False, instance_uuid=None):
        if dst is True:
            self.agent.logger.info('before_migrate_entity_actions()', ' KVM Plugin - Before Migration Destination: '
                                                                     'Create Domain and destination files')
            uri = str('%s/%s/%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid, self.INSTANCE, instance_uuid))
            entity_info = json.loads(self.agent.dstore.get(uri))
            vm_info = entity_info.get("entity_data")

            entity = KVMLibvirtEntity(instance_uuid, vm_info.get('name'), vm_info.get('cpu'),
                                      vm_info.get('memory'), '', vm_info.get('disk_size'), '',
                                      vm_info.get('networks'),
                                      vm_info.get('base_image'), vm_info.get('user-data'), vm_info.get('ssh-key'))
            entity.state = State.DEFINED
            image_name = os.path.join(self.BASE_DIR, self.IMAGE_DIR, entity.image.split('/')[-1])
            self.agent.get_os_plugin().download_file(entity.image_url, image_name)
            entity.image = image_name
            self.current_entities.update({entity_uuid: entity})
            self.__update_actual_store(entity_uuid, entity_info)


            id = len(entity.instances)
            name = '{0}{1}'.format(entity.name, id)
            disk_path = str('%s.qcow2' % instance_uuid)
            cdrom_path = str('%s_config.iso' % instance_uuid)
            disk_path = os.path.join(self.BASE_DIR, self.DISK_DIR, disk_path)
            cdrom_path = os.path.join(self.BASE_DIR, self.DISK_DIR, cdrom_path)
            instance = KVMLibvirtEntityInstance(instance_uuid, name, vm_info.get('cpu'),
                vm_info.get('memory'),disk_path,vm_info.get('disk_size'), cdrom_path, vm_info.get('networks'),
                vm_info.get('base_image'), vm_info.get('user-data'), vm_info.get('ssh-key'),entity_uuid)

            instance.state = State.LANDING
            vm_info.update({"name": name})
            vm_xml = self.__generate_dom_xml(instance)

            instance.xml = vm_xml
            qemu_cmd = str("qemu-img create -f qcow2 %s %dG" % (instance.disk, instance.disk_size))
            self.agent.get_os_plugin().execute_command(qemu_cmd, True)
            self.agent.get_os_plugin().create_file(instance.cdrom)
            self.agent.get_os_plugin().create_file(os.path.join(self.BASE_DIR, self.LOG_DIR, str('%s_log.log' % instance_uuid)))

            conf_cmd = str("%s --hostname %s --uuid %s" % (os.path.join(self.DIR, 'templates',
                                                           'create_config_drive.sh'), instance.name, instance_uuid))
            rm_temp_cmd = str("rm")
            if instance.user_file is not None and instance.user_file != '':
                data_filename = str("userdata_%s" % instance_uuid)
                self.agent.get_os_plugin().store_file(instance.user_file, self.BASE_DIR, data_filename)
                data_filename = os.path.join(self.BASE_DIR, data_filename)
                conf_cmd = str(conf_cmd + " --user-data %s" % data_filename)
                # rm_temp_cmd = str(rm_temp_cmd + " %s" % data_filename)
            if instance.ssh_key is not None and instance.ssh_key != '':
                key_filename = str("key_%s.pub" % instance_uuid)
                self.agent.get_os_plugin().store_file(instance.ssh_key, self.BASE_DIR, key_filename)
                key_filename = os.path.join(self.BASE_DIR, key_filename)
                conf_cmd = str(conf_cmd + " --ssh-key %s" % key_filename)
                # rm_temp_cmd = str(rm_temp_cmd + " %s" % key_filename)

            conf_cmd = str(conf_cmd + " %s" % instance.cdrom)

            self.agent.get_os_plugin().execute_command(qemu_cmd, True)
            #self.agent.getOSPlugin().createFile(entity.cdrom)

            self.agent.get_os_plugin().execute_command(conf_cmd, True)


            # try:
            #     self.conn.defineXML(vm_xml)
            # except libvirt.libvirtError as err:
            #     self.conn = libvirt.open("qemu:///system")
            #     self.conn.defineXML(vm_xml)

            entity_info.update({"entity_data": vm_info})
            entity_info.update({"status": "landing"})

            entity.add_instance(instance)
            self.current_entities.update({entity_uuid: entity})

            self.__update_actual_store_instance(entity_uuid,instance_uuid, entity_info)

            return True
        else:
            self.agent.logger.info('before_migrate_entity_actions()', ' KVM Plugin - Before Migration Source: get '
                                                                     'information about destination node')
            entity = self.current_entities.get(entity_uuid, None)
            instance = entity.get_instance(instance_uuid)
            uri = str("%s/%s/%s/%s/%s" % (self.agent.dhome, self.HOME, entity_uuid, self.INSTANCE, instance_uuid))
            instance_info = json.loads(self.agent.dstore.get(uri))
            fognode_uuid = instance_info.get("dst")

            uri = str('afos://<sys-id>/%s/plugins' % fognode_uuid)
            all_plugins = json.loads(self.agent.astore.get(uri)).get('plugins') # TODO: solve this ASAP

            runtimes = [x for x in all_plugins if x.get('type') == 'runtime']
            search = [x for x in runtimes if 'KVMLibvirt' in x.get('name')]
            if len(search) == 0:
                self.agent.logger.error('before_migrate_entity_actions()', 'KVM Plugin - Before Migration Source: No '
                                                                          'KVM Plugin, Aborting!!!')
                exit()
            else:
                kvm = search[0]

            #uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (dst, kvm.get('uuid'), entity_uuid))
            #self.agent.dstore.put(uri, instance_info)

            flag = False
            while flag:
                self.agent.logger.info('before_migrate_entity_actions()', ' KVM Plugin - Before Migration Source: '
                                                                         'Waiting destination to be '
                                        'ready')
                time.sleep(1)
                uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s/instance/%s" % (dst, kvm.get('uuid'), entity_uuid,
                                                                                   instance_uuid))
                vm_info = json.loads(self.agent.astore.get(uri)) # TODO: solve this ASAP
                if vm_info is not None and vm_info.get("status") == "landing":
                        flag = True

            instance.state = State.TAKING_OFF
            instance_info.update({'status' : 'taking_off'})
            self.__update_actual_store_instance(entity_uuid,instance_uuid,instance_info)

            self.current_entities.update({entity_uuid: entity})
            uri = str("afos://<sys-id>/%s/" % fognode_uuid)

            dst_node_info = self.agent.astore.get(uri) # TODO: solve this ASAP
            if isinstance(dst_node_info, tuple):
                dst_node_info = dst_node_info[0]
            dst_node_info = dst_node_info.replace("'", '"')
            #print(dst_node_info)
            dst_node_info = json.loads(dst_node_info)
            ## json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)
            # dst_node_info = json.loads(self.agent.astore.get(uri)[0])
            ##
            dom = self.__lookup_by_uuid(instance_uuid)
            nw = dst_node_info.get('network')

            dst_hostname = dst_node_info.get('name')



            dst_ip = [x for x in nw if x.get("default_gw") is True]
            # TODO: or x.get("inft_configuration").get("ipv6_gateway") for ip_v6
            if len(dst_ip) == 0:
                return False

            dst_ip = dst_ip[0].get("inft_configuration").get("ipv4_address") # TODO: as on search should use ipv6

            # ## ADDING TO /etc/hosts otherwise migration can fail
            self.agent.get_os_plugin().add_know_host(dst_hostname, dst_ip)
            ###

            # ## ACTUAL MIGRATIION ##################
            dst_host = str('qemu+ssh://%s/system' % dst_ip)
            dest_conn = libvirt.open(dst_host)
            if dest_conn is None:
                self.agent.logger.error('before_migrate_entity_actions()', 'KVM Plugin - Before Migration Source: '
                                                                          'Error on libvirt connection')
                exit(1)
            new_dom = dom.migrate(dest_conn,
                                  libvirt.VIR_MIGRATE_LIVE and libvirt.VIR_MIGRATE_PERSIST_DEST and libvirt.VIR_MIGRATE_NON_SHARED_DISK,
                                                                        entity.name, None, 0)
            if new_dom is None:
                self.agent.logger.error('before_migrate_entity_actions()', 'KVM Plugin - Before Migration Source: '
                                                                          'Migration failed')
                exit(1)

                self.agent.logger.info('before_migrate_entity_actions()', ' KVM Plugin - Before Migration Source: '
                                                                         'Migration succeeds')
            dest_conn.close()
            # #######################################

            # ## REMOVING AFTER MIGRATION
            self.agent.get_os_plugin().remove_know_host(dst_hostname)
            instance.on_stop()
            self.current_entities.update({entity_uuid: entity})

            return True

    def after_migrate_entity_actions(self, entity_uuid, dst=False, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('after_migrate_entity_actions()', 'KVM Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('after_migrate_entity_actions()', 'KVM Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in correct state",
                                                     str("Entity %s is not in correct state" % entity.get_state()))
        else:
            if dst is True:

                instance = entity.get_instance(instance_uuid)
                '''
                Here the plugin also update to the current status, and remove unused keys
                '''
                self.agent.logger.info('after_migrate_entity_actions()', ' KVM Plugin - After Migration Destination: Updating state')
                instance.on_start()


                self.current_entities.update({entity_uuid: entity})

                uri = str('%s/%s/%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid,self.INSTANCE,instance_uuid))
                vm_info = json.loads(self.agent.dstore.get(uri))
                vm_info.pop('dst')
                vm_info.update({"status": "run"})

                self.__update_actual_store_instance(entity_uuid,instance_uuid, vm_info)
                self.current_entities.update({entity_uuid: entity})

                return True
            else:
                '''
                Source node destroys all information about vm
                '''
                self.agent.logger.info('after_migrate_entity_actions()', ' KVM Plugin - After Migration Source: Updating state, destroy vm')
                self.__force_entity_instance_termination(entity_uuid,instance_uuid)
                return True

    def __react_to_cache(self, uri, value, v):
        self.agent.logger.info('__react_to_cache()', ' KVM Plugin - React to to URI: %s Value: %s Version: %s' % (uri, value, v))
        if uri.split('/')[-2] == 'entity':
            if value is None and v is None:
                self.agent.logger.info('__react_to_cache()', ' KVM Plugin - This is a remove for URI: %s' % uri)
                entity_uuid = uri.split('/')[-1]
                self.undefine_entity(entity_uuid)
            else:
                uuid = uri.split('/')[-1]
                value = json.loads(value)
                action = value.get('status')
                entity_data = value.get('entity_data')
                #print(type(entity_data))
                react_func = self.__react(action)
                if react_func is not None and entity_data is None:
                    react_func(uuid)
                elif react_func is not None:
                    entity_data.update({'entity_uuid': uuid})
                    if action == 'define':
                        react_func(**entity_data)
                    # else:
                    #     if action == 'landing':
                    #         react_func(entity_data, dst=True)
                    #     else:
                    #             react_func(entity_data)
        elif uri.split('/')[-2] == 'instance':
            if value is None and v is None:
                self.agent.logger.info('__react_to_cache()', ' KVM Plugin - This is a remove for URI: %s' % uri)
                instance_uuid = uri.split('/')[-1]
                entity_uuid = uri.split('/')[-3]
                self.__force_entity_instance_termination(entity_uuid,instance_uuid)
            else:
                instance_uuid = uri.split('/')[-1]
                entity_uuid = uri.split('/')[-3]
                value = json.loads(value)
                action = value.get('status')
                entity_data = value.get('entity_data')
                #print(type(entity_data))
                react_func = self.__react(action)
                if react_func is not None and entity_data is None:
                    react_func(entity_uuid, instance_uuid)
                elif react_func is not None:
                    entity_data.update({'entity_uuid': entity_uuid})
                    if action == 'landing':
                        react_func(entity_data, dst=True, instance_uuid=instance_uuid)
                    else:
                        react_func(entity_data, instance_uuid=instance_uuid)

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

    # def __generate_dom_xml(self, entity):
    #     template_xml = self.agent.getOSPlugin().readFile(os.path.join(self.DIR, 'templates', 'vm.xml'))
    #     vm_xml = Environment().from_string(template_xml)
    #     vm_xml = vm_xml.render(name=entity.name, uuid=entity.uuid, memory=entity.ram,
    #                            cpu=entity.cpu, disk_image=entity.disk,
    #                            iso_image=entity.cdrom, networks=entity.networks)
    #     return vm_xml

    def __force_entity_instance_termination(self, entity_uuid, instance_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('stop_entity()', ' KVM Plugin - Stop a VM uuid %s ' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('stop_entity()', 'KVM Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        else:
            if instance_uuid is None or not entity.has_instance(instance_uuid):
                self.agent.logger.error('run_entity()', 'KVM Plugin - Instance not found!!')
            else:
                instance = entity.get_instance(instance_uuid)
                if instance.get_state() == State.PAUSED:
                    self.resume_entity(entity_uuid, instance_uuid)
                    self.stop_entity(entity_uuid, instance_uuid)
                    self.clean_entity(entity_uuid, instance_uuid)
                #    self.undefine_entity(k)
                if instance.get_state() == State.RUNNING:
                    self.stop_entity(entity_uuid, instance_uuid)
                    self.clean_entity(entity_uuid, instance_uuid)
                #    self.undefine_entity(k)
                if instance.get_state() == State.CONFIGURED:
                    self.clean_entity(entity_uuid, instance_uuid)
                #    self.undefine_entity(k)
                #if instance.get_state() == State.DEFINED:
                #    self.undefine_entity(k)


    def __generate_dom_xml(self, instance):
        template_xml = self.agent.get_os_plugin().read_file(os.path.join(self.DIR, 'templates', 'vm.xml'))
        vm_xml = Environment().from_string(template_xml)
        vm_xml = vm_xml.render(name=instance.name, uuid=instance.uuid, memory=instance.ram,
                               cpu=instance.cpu, disk_image=instance.disk,
                               iso_image=instance.cdrom, networks=instance.networks)
        return vm_xml

    def __update_actual_store(self, uri, value):
        uri = str("%s/%s/%s" % (self.agent.ahome, self.HOME, uri))
        value = json.dumps(value)
        self.agent.astore.put(uri, value)

    def __update_actual_store_instance(self, entity_uuid, instance_uuid, value):
        uri = str("%s/%s/%s/%s/%s" % (self.agent.ahome, self.HOME, entity_uuid, self.INSTANCE, instance_uuid))
        value = json.dumps(value)
        self.agent.astore.put(uri, value)

    def __pop_actual_store(self, entity_uuid):
        #e = uri
        uri = str("%s/%s/%s" % (self.agent.ahome, self.HOME, entity_uuid))
        self.agent.astore.remove(uri)
        #uri = str("%s/%s/%s" % (self.agent.dhome, self.HOME, e))
        #self.agent.dstore.remove(uri)

    def __pop_actual_store_instance(self, entity_uuid, instance_uuid):
        # e = uri
        uri = str("%s/%s/%s/%s/%s" % (self.agent.ahome, self.HOME, entity_uuid, self.INSTANCE, instance_uuid))
        self.agent.astore.remove(uri)

    def __netmask_to_cidr(self, netmask):
        return sum([bin(int(x)).count('1') for x in netmask.split('.')])

    def __react(self, action):
        r = {
            'define': self.define_entity,
            'configure': self.configure_entity,
            'clean': self.clean_entity,
            'undefine': self.undefine_entity,
            'stop': self.stop_entity,
            'resume': self.resume_entity,
            'run': self.run_entity,
            'landing': self.migrate_entity,
            'taking_off': self.migrate_entity
        }

        return r.get(action, None)
