import sys
import os
import uuid
import psutil
import json
sys.path.append(os.path.join(sys.path[0], 'interfaces'))
from States import State
from RuntimePlugin import *
from ROS2Entity import ROS2Entity



class ROS2(RuntimePlugin):

    def __init__(self, name, version, agent):
        super(ROS2, self).__init__(version)
        self.uuid = uuid.uuid4()
        self.name = name
        self.agent = agent

        self.BASE_DIR = "/opt/fos/ros2"
        self.NODLETS_DIR = "nodlets"
        self.LOG_DIR = "logs"

        self.HOME = str("runtime/%s/entity" % self.uuid)
        self.startRuntime()

    def startRuntime(self):
        uri = str('%s/%s/*' % (self.agent.dhome, self.HOME))
        print("ROS2 Listening on %s" % uri)

        #source /opt/ros/r2b3/setup.bash
        #source /opt/ros/r2b3/share/ros2cli/environment/ros2-argcomplete.bash

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
        print ("Stopping ROS2 runtime...")
        return True

    def defineEntity(self, *args, **kwargs):

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

        return entity_uuid

    def undefineEntity(self, entity_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.DEFINED:
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state",
                                                     str("Entity %s is not in DEFINED state" % entity_uuid))
        else:
            self.current_entities.pop(entity_uuid, None)
            #self.__pop_actual_store(entity_uuid)
            return True

    def configureEntity(self, entity_uuid):

        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')

        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.DEFINED:
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state",
                                                     str("Entity %s is not in DEFINED state" % entity_uuid))
        else:


            self.agent.getOSPlugin().createFile(entity.outfile)
            ## download the nodelet file
            nodelet_dir = str("%s/%s/%s" % (self.BASE_DIR, self.LOG_DIR, entity_uuid))
            self.agent.getOSPlugin().createDir(nodelet_dir)
            wget_cmd = str('wget %s -O %s/' % (entity.url, nodelet_dir))
            self.agent.getOSPlugin().executeCommand(wget_cmd, True)
            ## unzip it?


            entity.onConfigured()
            self.current_entities.update({entity_uuid: entity})
            uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
            na_info = json.loads(self.agent.dstore.get(uri))
            na_info.update({"status": "configured"})
            self.__update_actual_store(entity_uuid, na_info)
            return True

    def cleanEntity(self, entity_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')

        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.CONFIGURED:
            raise StateTransitionNotAllowedException("Entity is not in CONFIGURED state",
                                                     str("Entity %s is not in CONFIGURED state" % entity_uuid))
        else:

            self.agent.getOSPlugin().removeFile(entity.outfile)
            nodelet_dir = str("%s/%s/%s" % (self.BASE_DIR, self.LOG_DIR, entity_uuid))
            self.agent.getOSPlugin().removeDir(nodelet_dir)
            entity.onClean()
            self.current_entities.update({entity_uuid: entity})

            uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
            na_info = json.loads(self.agent.dstore.get(uri))
            na_info.update({"status": "cleaned"})
            self.__update_actual_store(entity_uuid, na_info)

            return True

    def runEntity(self, entity_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        entity = self.current_entities.get(entity_uuid,None)
        if entity is None:
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.CONFIGURED:
            raise StateTransitionNotAllowedException("Entity is not in CONFIGURED state",
                                                     str("Entity %s is not in CONFIGURED state" % entity_uuid))
        else:

            cmd = str("ros2 run %s %s" % (entity.command, ' '.join(str(x) for x in entity.args)))
            process = self.__execute_command(cmd, entity.outfile)
            entity.onStart(process.pid, process)
            self.current_entities.update({entity_uuid: entity})
            uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
            na_info = json.loads(self.agent.dstore.get(uri))
            na_info.update({"status": "run"})
            self.__update_actual_store(entity_uuid, na_info)
            return True

    def stopEntity(self, entity_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.RUNNING:
            raise StateTransitionNotAllowedException("Entity is not in RUNNING state",
                                                     str("Entity %s is not in RUNNING state" % entity_uuid))
        else:
            p = entity.process
            p.terminate()
            entity.onStop()
            self.current_entities.update({entity_uuid: entity})
            uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
            na_info = json.loads(self.agent.dstore.get(uri))
            na_info.update({"status": "stop"})
            self.__update_actual_store(entity_uuid, na_info)
            return True

    def pauseEntity(self, entity_uuid):
        print("Can't pause a native application")
        return False

    def resumeEntity(self, entity_uuid):
        print("Can't resume a native application")
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
        print("Native on React \nURI:%s\nValue:%s\nVersion:%s" % (uri, value, v))
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





