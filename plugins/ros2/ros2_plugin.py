import sys
import os
import uuid
import psutil
import json
from fog05.interfaces.States import State
from fog05.interfaces.RuntimePlugin import *
from ROS2Entity import ROS2Entity
from ROS2EntityInstance import ROS2EntityInstance
from jinja2 import Environment



class ROS2(RuntimePlugin):

    def __init__(self, name, version, agent, plugin_uuid):
        super(ROS2, self).__init__(version, plugin_uuid)
        self.name = name
        self.agent = agent
        self.agent.logger.info('__init__()', ' Hello from ROS2 Plugin')
        self.BASE_DIR = os.path.join(self.agent.base_path, 'ros2')
        self.NODLETS_DIR = "nodlets"
        self.LOG_DIR = "logs"

        file_dir = os.path.dirname(__file__)
        self.DIR = os.path.abspath(file_dir)

        self.HOME = str("runtime/%s/entity" % self.uuid)
        self.INSTANCE = "instance"
        self.start_runtime()

    def start_runtime(self):
        uri = str('%s/%s/*' % (self.agent.dhome, self.HOME))

        #s_cmd = "source /opt/ros/r2b3/setup.bash"
        #self.agent.getOSPlugin().executeCommand(s_cmd, True)
        #s_cmd = "source /opt/ros/r2b3/share/ros2cli/environment/ros2-argcomplete.bash"
        #self.agent.getOSPlugin().executeCommand(s_cmd, True)

        #self.__shell_source("/opt/ros/r2b3/setup.bash")
        #self.__shell_source("/opt/ros/r2b3/share/ros2cli/environment/ros2-argcomplete.bash")
        '''
        These two files need to be sourced
        '''

        self.agent.logger.info('startRuntime()', ' ROS2 Plugin - Observing %s' % uri)
        self.agent.dstore.observe(uri, self.__react_to_cache)

        '''check if dirs exists if not exists create'''
        if self.agent.getOSPlugin().dirExists(self.BASE_DIR):
            if not self.agent.getOSPlugin().dirExists(os.path.join(self.BASE_DIR, self.NODLETS_DIR)):
                self.agent.getOSPlugin().createDir(os.path.join(self.BASE_DIR, self.NODLETS_DIR))
            if not self.agent.getOSPlugin().dirExists(os.path.join(self.BASE_DIR, self.LOG_DIR)):
                self.agent.getOSPlugin().createDir(os.path.join(self.BASE_DIR, self.LOG_DIR))
        else:
            self.agent.getOSPlugin().createDir(str("%s") % self.BASE_DIR)
            self.agent.getOSPlugin().createDir(os.path.join(self.BASE_DIR, self.NODLETS_DIR))
            self.agent.getOSPlugin().createDir(os.path.join(self.BASE_DIR, self.LOG_DIR))

    def stop_runtime(self):
        self.agent.logger.info('stopRuntime()', ' ROS2 Plugin - Destroy running entities')
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
        self.agent.logger.info('stopRuntime()', '[ DONE ] ROS2 Plugin - Bye')
        return True

    def define_entity(self, *args, **kwargs):
        self.agent.logger.info('defineEntity()', ' ROS2 Plugin - Define ROS2 Nodelets')
        if len(kwargs) > 0:
            entity_uuid = kwargs.get('entity_uuid')
            out_file = str('ros2_%s.log', entity_uuid)
            out_file = os.path.join(self.BASE_DIR, self.LOG_DIR, out_file)
            entity = ROS2Entity(entity_uuid, kwargs.get('name'), kwargs.get('command'), kwargs.get('args'),
                                out_file, kwargs.get('url'))
        else:
            return None

        nodelet_dir = os.path.join(self.BASE_DIR, self.NODLETS_DIR, entity_uuid)
        self.agent.getOSPlugin().createDir(nodelet_dir)
        # wget_cmd = str('wget %s -O %s/%s' % (entity.url, nodelet_dir, entity.url.split('/')[-1]))
        # self.agent.getOSPlugin().executeCommand(wget_cmd, True)
        self.agent.getOSPlugin().downloadFile(
            entity.image, os.path.join(self.BASE_DIR, self.NODLETS_DIR, entity.url.split('/')[-1]))

        unzip_cmd = str("unzip %s/%s -d %s" % (nodelet_dir, entity.url.split('/')[-1], nodelet_dir))
        self.agent.getOSPlugin().executeCommand(unzip_cmd, True)
        '''
        ament_cmd = str("ament build_pkg %s/%s" % (nodelet_dir, entity_uuid))
        self.agent.getOSPlugin().executeCommand(ament_cmd, True)

        At the moment using the generated bash script for build
        '''
        path = os.path.join(nodelet_dir, entity.url.split('/')[-1].split('.')[0])
        build_script = self.__generate_build_script(path, nodelet_dir)
        self.agent.getOSPlugin().storeFile(build_script, nodelet_dir, str("%s_build.sh" % entity_uuid))
        chmod_cmd = str("chmod +x %s" % os.path.join(nodelet_dir, str("%s_build.sh" % entity_uuid)))
        self.agent.getOSPlugin().executeCommand(chmod_cmd, True)
        build_cmd = os.path.join(nodelet_dir, str("%s_build.sh" % entity_uuid))
        self.agent.getOSPlugin().executeCommand(build_cmd, True)

        entity.set_state(State.DEFINED)
        self.current_entities.update({entity_uuid: entity})
        uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
        na_info = json.loads(self.agent.dstore.get(uri))
        na_info.update({"status": "defined"})
        self.__update_actual_store(entity_uuid, na_info)
        self.agent.logger.info('defineEntity()', '[ DONE ] ROS2 Plugin - Define ROS2 Nodelets uuid %s' % entity_uuid)
        return entity_uuid

    def undefine_entity(self, entity_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('undefineEntity()', ' ROS2 Plugin - Undefine ROS2 Nodelets uuid %s' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('undefineEntity()', 'ROS2 Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('undefineEntity()', 'ROS2 Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state",
                                                     str("Entity %s is not in DEFINED state" % entity_uuid))
        else:
            self.current_entities.pop(entity_uuid, None)
            self.__pop_actual_store(entity_uuid)
            self.agent.logger.info('undefineEntity()', 'ROS2 Plugin - Undefine ROS2 Nodelets uuid %s' % entity_uuid)
            return True

    def configure_entity(self, entity_uuid, instance_uuid=None):

        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('configureEntity()', ' ROS2 Plugin - Configure ROS2 Nodelets uuid %s' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('configureEntity()', 'ROS2 Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.get_state() != State.DEFINED:
            self.agent.logger.error('configureEntity()', 'ROS2 Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state",
                                                     str("Entity %s is not in DEFINED state" % entity_uuid))
        else:

            if instance_uuid is None:
                instance_uuid = str(uuid.uuid4())

            if entity.has_instance(instance_uuid):
                print("This instance already existis!!")
            else:
                id = len(entity.instances)
                out_file = str("native_%s_%s.log" % entity_uuid, instance_uuid)
                out_file = os.path.join(self.BASE_DIR, self.LOG_DIR, out_file)
                #nodelet_dir = os.path.join(self.BASE_DIR, self.NODLETS_DIR, entity_uuid)
                #cmd = os.path.join(nodelet_dir,entity.command)
                #uuid, name, command, args, outfile, url, entity_uuid)
                instance = ROS2EntityInstance(instance_uuid, entity.name + id, entity.command, entity.args,
                                              entity.url, out_file, entity_uuid)


                self.agent.getOSPlugin().createFile(entity.outfile)
                ## download the nodelet file
                # nodelet_dir = os.path.join(self.BASE_DIR, self.NODLETS_DIR, entity_uuid)
                # self.agent.getOSPlugin().createDir(nodelet_dir)
                # #wget_cmd = str('wget %s -O %s/%s' % (entity.url, nodelet_dir, entity.url.split('/')[-1]))
                # #self.agent.getOSPlugin().executeCommand(wget_cmd, True)
                # self.agent.getOSPlugin().downloadFile(
                #     entity.image, os.path.join(self.BASE_DIR, self.IMAGE_DIR,entity.url.split('/')[-1]))
                '''
                from https://github.com/ros2/examples
                I tried to run some c++ example, here the workflow
                ament build_pkg example_directory
                cd install/libs
                ./example_executable
                 
                 and it seems to run, i'll try to make these steps here
                 
                 
                 test nodes 
                 
                 http://172.16.7.128/minimal_publisher.zip
                 http://172.16.7.128/minimal_subscriber.zip
                '''
                # unzip_cmd = str("unzip %s/%s -d %s" % (nodelet_dir, entity.url.split('/')[-1], nodelet_dir))
                # self.agent.getOSPlugin().executeCommand(unzip_cmd, True)
                # '''
                # ament_cmd = str("ament build_pkg %s/%s" % (nodelet_dir, entity_uuid))
                # self.agent.getOSPlugin().executeCommand(ament_cmd, True)
                #
                # At the moment using the generated bash script for build
                # '''
                # path = os.path.join(nodelet_dir, entity.url.split('/')[-1].split('.')[0])
                # build_script = self.__generate_build_script(path, nodelet_dir)
                # self.agent.getOSPlugin().storeFile(build_script, nodelet_dir, str("%s_build.sh" % entity_uuid))
                # chmod_cmd = str("chmod +x %s" % os.path.join(nodelet_dir, str("%s_build.sh" % entity_uuid)))
                # self.agent.getOSPlugin().executeCommand(chmod_cmd, True)
                # build_cmd = os.path.join(nodelet_dir, str("%s_build.sh" % entity_uuid))
                # self.agent.getOSPlugin().executeCommand(build_cmd, True)

                ### this is only a workaround not a real solution

                instance.on_configured()
                entity.add_instance(instance)
                self.current_entities.update({entity_uuid: entity})
                uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
                na_info = json.loads(self.agent.dstore.get(uri))
                na_info.update({"status": "configured"})
                self.__update_actual_store_instance(entity_uuid, instance_uuid, na_info)
                self.agent.logger.info('configureEntity()', '[ DONE ] ROS2 Plugin - Configure ROS2 Nodelets uuid %s' % instance_uuid)
                return True

    def clean_entity(self, entity_uuid, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('cleanEntity()', ' ROS2 Plugin - Clean ROS2 Nodelets uuid %s' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('cleanEntity()', 'ROS2 Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.get_state() != State.CONFIGURED:
            self.agent.logger.error('cleanEntity()', 'ROS2 Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in CONFIGURED state",
                                                     str("Entity %s is not in CONFIGURED state" % entity_uuid))
        else:
            if instance_uuid is None or not entity.has_instance(instance_uuid):
                self.agent.logger.error('clean_entity()','Native Plugin - Instance not found!!')
            else:
                instance = entity.get_instance(instance_uuid)
                if instance.get_state() != State.CONFIGURED:
                    self.agent.logger.error('clean_entity()',
                                        'has_instance Plugin - Instance state is wrong, or transition not allowed')
                    raise StateTransitionNotAllowedException("Instance is not in CONFIGURED state",
                                                         str("Instance %s is not in CONFIGURED state" % instance_uuid))
                else:
                    self.agent.getOSPlugin().removeFile(instance.outfile)
                    #nodelet_dir = str("%s/%s/%s" % (self.BASE_DIR, self.NODLETS_DIR, entity_uuid))
                    #self.agent.getOSPlugin().removeDir(nodelet_dir)
                    instance.on_clean()
                    entity.remove_instance(instance)
                    self.current_entities.update({entity_uuid: entity})

                    #uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
                    #na_info = json.loads(self.agent.dstore.get(uri))
                    #na_info.update({"status": "cleaned"})
                    self.__pop_actual_store_instance(entity_uuid, instance_uuid)
                    self.agent.logger.info('cleanEntity()', '[ DONE ] ROS2 Plugin - Clean ROS2 Nodelets uuid %s' % instance_uuid)
                    return True

    def run_entity(self, entity_uuid, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('runEntity()', ' ROS2 Plugin - Starting ROS2 Nodelets uuid %s' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('runEntity()', 'ROS2 Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.get_state() != State.CONFIGURED:
            self.agent.logger.error('runEntity()', 'ROS2 Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in CONFIGURED state",
                                                     str("Entity %s is not in CONFIGURED state" % entity_uuid))
        else:

            instance = entity.get_instance(instance_uuid)
            if instance.get_state() != State.CONFIGURED:
                self.agent.logger.error('clean_entity()',
                                        'KVM Plugin - Instance state is wrong, or transition not allowed')
                raise StateTransitionNotAllowedException("Instance is not in CONFIGURED state",
                                                         str("Instance %s is not in CONFIGURED state" % instance_uuid))
            else:

                if instance.source is None:
                    cmd = str("%s %s" % (entity.command, ' '.join(str(x) for x in entity.args)))
                else:
                    #cmd = str("ros2 run %s %s" % (entity.command, ' '.join(str(x) for x in entity.args)))
                    nodelet_dir = os.path.join(self.BASE_DIR, self.NODLETS_DIR, entity_uuid)
                    cmd = os.path.join(nodelet_dir, 'lib', entity.name, instance.command)
                    path =os.path.join(self.BASE_DIR, self.NODLETS_DIR, instance_uuid, instance.name)
                    # ###################### WORKAROUND ##############################
                    run_script = self.__generate_run_script(cmd, path)
                    self.agent.getOSPlugin().storeFile(run_script, nodelet_dir, str("%s_run.sh" % instance_uuid))
                    chmod_cmd = str("chmod +x %s" % os.path.join(nodelet_dir, str("%s_run.sh" % instance_uuid)))
                    self.agent.getOSPlugin().executeCommand(chmod_cmd, True)
                    run_cmd = os.path.join(nodelet_dir, str("%s_run.sh" % instance_uuid))
                    # ################################################################


                    process = self.__execute_command(run_cmd, instance.outfile)
                    instance.on_start(process.pid, process)
                    self.current_entities.update({entity_uuid: entity})
                    uri = str('%s/%s/%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid, self.INSTANCE, instance_uuid))
                    na_info = json.loads(self.agent.dstore.get(uri))
                    na_info.update({"status": "run"})
                    self.__update_actual_store_instance(entity_uuid, instance_uuid, na_info)
                    self.agent.logger.info('runEntity()', '[ DONE ] ROS2 Plugin - Started ROS2 Nodelets uuid %s' % instance_uuid)
                    return True

    def stop_entity(self, entity_uuid, instance_uuid=None):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('stopEntity()', ' ROS2 Plugin - Stopping ROS2 Nodelets uuid %s' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('stopEntity()', 'ROS2 Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.get_state() != State.RUNNING:
            self.agent.logger.error('stopEntity()', 'ROS2 Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in RUNNING state",
                                                     str("Entity %s is not in RUNNING state" % entity_uuid))
        else:

            instance = entity.get_instance(instance_uuid)
            if instance.get_state() != State.CONFIGURED:
                self.agent.logger.error('clean_entity()',
                                        'KVM Plugin - Instance state is wrong, or transition not allowed')
                raise StateTransitionNotAllowedException("Instance is not in CONFIGURED state",
                                                         str("Instance %s is not in CONFIGURED state" % instance_uuid))
            else:

                if instance.source is None:
                    cmd = str("%s %s" % (instance.command, ' '.join(str(x) for x in instance.args)))
                else:
                    path = str('%s.pid' % instance.name)
                    path = os.path.join(self.BASE_DIR, self.NODLETS_DIR, instance_uuid, path)
                    pid = int(self.agent.getOSPlugin().readFile(path))
                    self.agent.getOSPlugin().sendSigKill(pid)
                    '''
                    p = entity.process
        
                    p.terminate()  #process don't die
                    #os.kill(p.pid, 9)
                    #####
                    os.system(str("kill -9 %d" % p.pid ))
                    p.wait()
        
                    print(p.pid)    ## is different from the one in ps -ax why????
                    print(p.ppid()) ##
        
                    ####
                    '''
                    instance.on_stop()
                    self.current_entities.update({entity_uuid: entity})
                    uri = str('%s/%s/%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid, self.INSTANCE, instance_uuid))
                    na_info = json.loads(self.agent.dstore.get(uri))
                    na_info.update({"status": "stop"})
                    self.__update_actual_store_instance(entity_uuid, instance_uuid, na_info)
                    self.agent.logger.info('stopEntity()', '[ DONE ] ROS2 Plugin - Clean ROS2 Nodelet uuid %s' % instance_uuid)
                    return True

    def pause_entity(self, entity_uuid, instance_uuid=None):
        self.agent.logger.warning('pauseEntity()', 'ROS2 Plugin - Cannot pause a ROS2 Nodelet')
        return False

    def resume_entity(self, entity_uuid, instance_uuid=None):
        self.agent.logger.warning('resumeEntity()', 'ROS2 Plugin - Cannot pause a ROS2 Nodelet')
        return False



    def __update_actual_store(self, uri, value):
        uri = str("%s/%s/%s" % (self.agent.ahome, self.HOME, uri))
        value = json.dumps(value)
        self.agent.astore.put(uri, value)

    def __pop_actual_store(self, uri,):
        uri = str("%s/%s/%s" % (self.agent.ahome, self.HOME, uri))
        self.agent.astore.remove(uri)

    def __update_actual_store_instance(self, entity_uuid, instance_uuid, value):
        uri = str("%s/%s/%s/%s/%s" % (self.agent.ahome, self.HOME, entity_uuid, self.INSTANCE, instance_uuid))
        value = json.dumps(value)
        self.agent.astore.put(uri, value)

    def __pop_actual_store_instance(self, entity_uuid, instance_uuid,):
        uri = str("%s/%s/%s/%s/%s" % (self.agent.ahome, self.HOME, entity_uuid, self.INSTANCE, instance_uuid))
        self.agent.astore.remove(uri)

    def __execute_command(self, command, out_file):
        f = open(out_file, 'w')
        cmd_splitted = command.split()
        p = psutil.Popen(cmd_splitted, stdout=f)
        return p

    def __react_to_cache(self, uri, value, v):
        self.agent.logger.info('__react_to_cache()', ' ROS2 Plugin - React to to URI: %s Value: %s Version: %s' % (uri, value, v))
        if uri.split('/')[-2] == 'entity':
            if value is None and v is None:
                self.agent.logger.info('__react_to_cache()', ' ROS2 Plugin - This is a remove for URI: %s' % uri)
                entity_uuid = uri.split('/')[-1]
                self.undefine_entity(entity_uuid)
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
                        react_func(entity_data)
        elif uri.split('/')[-2] == 'instance':
            if value is None and v is None:
                self.agent.logger.info('__react_to_cache()', ' ROS2 Plugin - This is a remove for URI: %s' % uri)
                instance_uuid = uri.split('/')[-1]
                entity_uuid = uri.split('/')[-3]
                self.__force_entity_instance_termination(entity_uuid, instance_uuid)
            else:
                instance_uuid = uri.split('/')[-1]
                entity_uuid = uri.split('/')[-3]
                value = json.loads(value)
                action = value.get('status')
                entity_data = value.get('entity_data')
                # print(type(entity_data))
                react_func = self.__react(action)
                if react_func is not None and entity_data is None:
                    react_func(entity_uuid, instance_uuid)
                elif react_func is not None:
                    entity_data.update({'entity_uuid': entity_uuid})

    def __generate_build_script(self, path, space):
        template_sh = self.agent.getOSPlugin().readFile(os.path.join(self.DIR, 'templates', 'build_ros.sh'))
        ros2_build = Environment().from_string(template_sh)
        ros2_build = ros2_build.render(node_path=path, space=space)
        return ros2_build

    def __generate_run_script(self, cmd, dir):
        template_sh = self.agent.getOSPlugin().readFile(os.path.join(self.DIR,'templates', 'run_ros.sh'))
        ros2_run = Environment().from_string(template_sh)
        ros2_run = ros2_run.render(command=cmd, path=dir)
        return ros2_run

    def __shell_source(self, script):
        """Sometime you want to emulate the action of "source" in bash,
        settings some environment variables. Here is a way to do it."""
        import subprocess, os
        pipe = subprocess.Popen(". %s; env" % script, stdout=subprocess.PIPE, shell=True)
        output = pipe.communicate()[0]
        env = dict((line.split(b"=", 1) for line in output.splitlines()))
        env = self.__convert(env)
        os.environ.update(env)

    def __convert(self, data):
        data_type = type(data)
        if data_type == bytes:
            return data.decode()
        if data_type in (str, int):
            return str(data)
        if data_type == dict:
            data = data.items()
        return data_type(map(self.convert, data))

    def __force_entity_instance_termination(self, entity_uuid, instance_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('__force_entity_instance_termination()', ' ROS2 Plugin - Stop a container uuid %s ' %
                               entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('__force_entity_instance_termination()', 'ROS2 Plugin - Entity not exists')
            raise EntityNotExistingException("Native not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        else:
            if instance_uuid is None or not entity.has_instance(instance_uuid):
                self.agent.logger.error('__force_entity_instance_termination()', 'ROS2 Plugin - Instance not found!!')
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



    def __react(self, action):
        r = {
            'define': self.define_entity,
            'configure': self.configure_entity,
            'clean': self.clean_entity,
            'undefine': self.undefine_entity,
            'stop': self.stop_entity,
            'resume': self.resume_entity,
            'run': self.run_entity
        }

        return r.get(action, None)





