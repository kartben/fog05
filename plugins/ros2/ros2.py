import sys
import os
import uuid
import psutil
import json
sys.path.append(os.path.join(sys.path[0], 'interfaces'))
from States import State
from RuntimePlugin import *
from ROS2Entity import ROS2Entity
from jinja2 import Environment



class ROS2(RuntimePlugin):

    def __init__(self, name, version, agent):
        super(ROS2, self).__init__(version)
        self.uuid = uuid.uuid4()
        self.name = name
        self.agent = agent
        self.agent.logger.info('[ INFO ] Hello from ROS2 Plugin')
        self.BASE_DIR = "/opt/fos/ros2"
        self.NODLETS_DIR = "nodlets"
        self.LOG_DIR = "logs"

        self.HOME = str("runtime/%s/entity" % self.uuid)
        self.startRuntime()

    def startRuntime(self):
        uri = str('%s/%s/*' % (self.agent.dhome, self.HOME))
        print("ROS2 Listening on %s" % uri)

        #s_cmd = "source /opt/ros/r2b3/setup.bash"
        #self.agent.getOSPlugin().executeCommand(s_cmd, True)
        #s_cmd = "source /opt/ros/r2b3/share/ros2cli/environment/ros2-argcomplete.bash"
        #self.agent.getOSPlugin().executeCommand(s_cmd, True)

        #self.__shell_source("/opt/ros/r2b3/setup.bash")
        #self.__shell_source("/opt/ros/r2b3/share/ros2cli/environment/ros2-argcomplete.bash")
        '''
        These two files need to be sourced
        '''

        self.agent.logger.info('[ INFO ] ROS2 Plugin - Observing %s' % uri)
        self.agent.dstore.observe(uri, self.__react_to_cache)

        '''check if dirs exists if not exists create'''
        if self.agent.getOSPlugin().dirExists(self.BASE_DIR):
            if not self.agent.getOSPlugin().dirExists(str("%s/%s") % (self.BASE_DIR, self.NODLETS_DIR)):
                self.agent.getOSPlugin().createDir(str("%s/%s") % (self.BASE_DIR, self.NODLETS_DIR))
            if not self.agent.getOSPlugin().dirExists(str("%s/%s") % (self.BASE_DIR, self.LOG_DIR)):
                self.agent.getOSPlugin().createDir(str("%s/%s") % (self.BASE_DIR, self.LOG_DIR))
        else:
            self.agent.getOSPlugin().createDir(str("%s") % self.BASE_DIR)
            self.agent.getOSPlugin().createDir(str("%s/%s") % (self.BASE_DIR, self.NODLETS_DIR))
            self.agent.getOSPlugin().createDir(str("%s/%s") % (self.BASE_DIR, self.LOG_DIR))

    def stopRuntime(self):
        self.agent.logger.info('[ INFO ] ROS2 Plugin - Destroy running entities')
        for k in list(self.current_entities.keys()):
            self.stopEntity(k)
            self.cleanEntity(k)
            self.undefineEntity(k)
        self.agent.logger.info('[ DONE ] ROS2 Plugin - Bye')
        return True

    def defineEntity(self, *args, **kwargs):
        self.agent.logger.info('[ INFO ] ROS2 Plugin - Define ROS2 Nodelets')
        if len(kwargs) > 0:
            entity_uuid = kwargs.get('entity_uuid')
            out_file = str("%s/%s/native_%s.log" % (self.BASE_DIR, self.LOG_DIR, entity_uuid))
            entity = ROS2Entity(entity_uuid, kwargs.get('name'), kwargs.get('command'), kwargs.get('args'),
                                out_file, kwargs.get('url'))
        else:
            return None

        entity.setState(State.DEFINED)
        self.current_entities.update({entity_uuid: entity})
        uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
        na_info = json.loads(self.agent.dstore.get(uri))
        na_info.update({"status": "defined"})
        self.__update_actual_store(entity_uuid, na_info)
        self.agent.logger.info('[ DONE ] ROS2 Plugin - Define ROS2 Nodelets uuid %s' % entity_uuid)
        return entity_uuid

    def undefineEntity(self, entity_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('[ INFO ] ROS2 Plugin - Undefine ROS2 Nodelets uuid %s' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('[ ERRO ] ROS2 Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.DEFINED:
            self.agent.logger.error('[ ERRO ] ROS2 Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state",
                                                     str("Entity %s is not in DEFINED state" % entity_uuid))
        else:
            self.current_entities.pop(entity_uuid, None)
            #self.__pop_actual_store(entity_uuid)
            self.agent.logger.info('[ DONE ] ROS2 Plugin - Undefine ROS2 Nodelets uuid %s' % entity_uuid)
            return True

    def configureEntity(self, entity_uuid):

        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('[ INFO ] ROS2 Plugin - Configure ROS2 Nodelets uuid %s' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('[ ERRO ] ROS2 Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.DEFINED:
            self.agent.logger.error('[ ERRO ] ROS2 Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state",
                                                     str("Entity %s is not in DEFINED state" % entity_uuid))
        else:


            self.agent.getOSPlugin().createFile(entity.outfile)
            ## download the nodelet file
            nodelet_dir = str("%s/%s/%s" % (self.BASE_DIR, self.NODLETS_DIR, entity_uuid))
            self.agent.getOSPlugin().createDir(nodelet_dir)
            wget_cmd = str('wget %s -O %s/%s' % (entity.url, nodelet_dir, entity.url.split('/')[-1]))
            self.agent.getOSPlugin().executeCommand(wget_cmd, True)
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
            unzip_cmd = str("unzip %s/%s -d %s" % (nodelet_dir, entity.url.split('/')[-1], nodelet_dir))
            self.agent.getOSPlugin().executeCommand(unzip_cmd, True)
            '''
            ament_cmd = str("ament build_pkg %s/%s" % (nodelet_dir, entity_uuid))
            self.agent.getOSPlugin().executeCommand(ament_cmd, True)
            
            At the moment using the generated bash script for build
            '''
            path = str("%s/%s" % (nodelet_dir, entity.url.split('/')[-1].split('.')[0]))
            build_script = self.__generate_build_script(path, nodelet_dir)
            self.agent.getOSPlugin().storeFile(build_script, nodelet_dir, str("%s_build.sh" % entity_uuid))
            chmod_cmd = str("chmod +x %s/%s" % (nodelet_dir, str("%s_build.sh" % entity_uuid)))
            self.agent.getOSPlugin().executeCommand(chmod_cmd, True)
            build_cmd = str("%s/%s" % (nodelet_dir, str("%s_build.sh" % entity_uuid)))
            self.agent.getOSPlugin().executeCommand(build_cmd, True)

            ### this is only a workaround not a real solution


            entity.onConfigured()
            self.current_entities.update({entity_uuid: entity})
            uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
            na_info = json.loads(self.agent.dstore.get(uri))
            na_info.update({"status": "configured"})
            self.__update_actual_store(entity_uuid, na_info)
            self.agent.logger.info('[ DONE ] ROS2 Plugin - Configure ROS2 Nodelets uuid %s' % entity_uuid)
            return True

    def cleanEntity(self, entity_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('[ INFO ] ROS2 Plugin - Clean ROS2 Nodelets uuid %s' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('[ ERRO ] ROS2 Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.CONFIGURED:
            self.agent.logger.error('[ ERRO ] ROS2 Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in CONFIGURED state",
                                                     str("Entity %s is not in CONFIGURED state" % entity_uuid))
        else:

            self.agent.getOSPlugin().removeFile(entity.outfile)
            nodelet_dir = str("%s/%s/%s" % (self.BASE_DIR, self.NODLETS_DIR, entity_uuid))
            self.agent.getOSPlugin().removeDir(nodelet_dir)
            entity.onClean()
            self.current_entities.update({entity_uuid: entity})

            uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
            na_info = json.loads(self.agent.dstore.get(uri))
            na_info.update({"status": "cleaned"})
            self.__update_actual_store(entity_uuid, na_info)
            self.agent.logger.info('[ DONE ] ROS2 Plugin - Clean ROS2 Nodelets uuid %s' % entity_uuid)
            return True

    def runEntity(self, entity_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('[ INFO ] ROS2 Plugin - Starting ROS2 Nodelets uuid %s' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('[ ERRO ] ROS2 Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.CONFIGURED:
            self.agent.logger.error('[ ERRO ] ROS2 Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in CONFIGURED state",
                                                     str("Entity %s is not in CONFIGURED state" % entity_uuid))
        else:

            #cmd = str("ros2 run %s %s" % (entity.command, ' '.join(str(x) for x in entity.args)))
            nodelet_dir = str("%s/%s/%s" % (self.BASE_DIR, self.NODLETS_DIR, entity_uuid))
            cmd = str("%s/lib/%s/%s" % (nodelet_dir, entity.name, entity.command))
            path = str("%s/%s/%s/%s" % (self.BASE_DIR, self.NODLETS_DIR, entity_uuid, entity.name))
            # ###################### WORKAROUND ##############################
            run_script = self.__generate_run_script(cmd, path)
            self.agent.getOSPlugin().storeFile(run_script, nodelet_dir, str("%s_run.sh" % entity_uuid))
            chmod_cmd = str("chmod +x %s/%s" % (nodelet_dir, str("%s_run.sh" % entity_uuid)))
            self.agent.getOSPlugin().executeCommand(chmod_cmd, True)
            run_cmd = str("%s/%s" % (nodelet_dir, str("%s_run.sh" % entity_uuid)))
            # ################################################################


            process = self.__execute_command(run_cmd, entity.outfile)
            entity.onStart(process.pid, process)
            self.current_entities.update({entity_uuid: entity})
            uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
            na_info = json.loads(self.agent.dstore.get(uri))
            na_info.update({"status": "run"})
            self.__update_actual_store(entity_uuid, na_info)
            self.agent.logger.info('[ DONE ] ROS2 Plugin - Started ROS2 Nodelets uuid %s' % entity_uuid)
            return True

    def stopEntity(self, entity_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('[ INFO ] ROS2 Plugin - Stopping ROS2 Nodelets uuid %s' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('[ ERRO ] ROS2 Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.RUNNING:
            self.agent.logger.error('[ ERRO ] ROS2 Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in RUNNING state",
                                                     str("Entity %s is not in RUNNING state" % entity_uuid))
        else:

            path = str("%s/%s/%s/%s.pid" % (self.BASE_DIR, self.NODLETS_DIR, entity_uuid, entity.name))
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
            entity.onStop()
            self.current_entities.update({entity_uuid: entity})
            uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
            na_info = json.loads(self.agent.dstore.get(uri))
            na_info.update({"status": "stop"})
            self.__update_actual_store(entity_uuid, na_info)
            self.agent.logger.info('[ DONE ] ROS2 Plugin - Clean ROS2 Nodelet uuid %s' % entity_uuid)
            return True

    def pauseEntity(self, entity_uuid):
        self.agent.logger.warning('[ WARN ] ROS2 Plugin - Cannot pause a ROS2 Nodelet')
        return False

    def resumeEntity(self, entity_uuid):
        self.agent.logger.warning('[ WARN ] ROS2 Plugin - Cannot pause a ROS2 Nodelet')
        return False



    def __update_actual_store(self, uri, value):
        uri = str("%s/%s/%s" % (self.agent.ahome, self.HOME, uri))
        value = json.dumps(value)
        self.agent.astore.put(uri, value)

    def __pop_actual_store(self, uri,):
        uri = str("%s/%s/%s" % (self.agent.ahome, self.HOME, uri))
        self.agent.astore.remove(uri)


    def __execute_command(self, command, out_file):
        f = open(out_file, 'w')
        cmd_splitted = command.split()
        p = psutil.Popen(cmd_splitted, stdout=f)
        return p

    def __react_to_cache(self, uri, value, v):
        self.agent.logger.info('[ INFO ] ROS2 Plugin - React to to URI: %s Value: %s Version: %s' % (uri, value, v))
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

    def __generate_build_script(self, path, space):
        template_xml = self.agent.getOSPlugin().readFile(os.path.join(sys.path[0], 'plugins', self.name,
                                                                      'templates', 'build_ros.sh'))
        vm_xml = Environment().from_string(template_xml)
        vm_xml = vm_xml.render(node_path=path, space=space)
        return vm_xml

    def __generate_run_script(self, cmd, dir):
        template_xml = self.agent.getOSPlugin().readFile(os.path.join(sys.path[0], 'plugins', self.name,
                                                                      'templates', 'run_ros.sh'))
        vm_xml = Environment().from_string(template_xml)
        vm_xml = vm_xml.render(command=cmd, path=dir)
        return vm_xml

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

        if data_type == bytes: return data.decode()
        if data_type in (str, int): return str(data)

        if data_type == dict: data = data.items()
        return data_type(map(self.convert, data))

    def __react(self, action):
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





