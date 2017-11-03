import sys
import os
import uuid
import psutil
import json
from fog05.interfaces.States import State
from fog05.interfaces.RuntimePlugin import *
from .NativeEntity import NativeEntity


class Native(RuntimePlugin):

    def __init__(self, name, version, agent):
        super(Native, self).__init__(version)
        self.uuid = uuid.uuid4()
        self.name = name
        self.agent = agent
        self.agent.logger.info('[ INFO ] Hello from Native Plugin')
        self.HOME = str("runtime/%s/entity" % self.uuid)
        self.startRuntime()

    def startRuntime(self):
        uri = str('%s/%s/*' % (self.agent.dhome, self.HOME))
        self.agent.logger.info('[ INFO ] Native Plugin - Observing %s' % uri)
        self.agent.dstore.observe(uri, self.__react_to_cache)
        return self.uuid

    def stopRuntime(self):
        self.agent.logger.info('[ INFO ] Native Plugin - Destroy running BE')
        for k in list(self.current_entities.keys()):
            self.stopEntity(k)
            self.cleanEntity(k)
            self.undefineEntity(k)
        self.agent.logger.info('[ DONE ] Native Plugin - Bye')
        return True

    def defineEntity(self, *args, **kwargs):

        if len(kwargs) > 0:
            entity_uuid = kwargs.get('entity_uuid')
            out_file = str("/opt/fos/logs/native_%s.log" % entity_uuid)
            entity = NativeEntity(entity_uuid, kwargs.get('name'), kwargs.get('command'), kwargs.get('args'), out_file)
        else:
            return None

        self.agent.logger.info('[ INFO ] Native Plugin - Define BE')
        entity.setState(State.DEFINED)
        self.current_entities.update({entity_uuid: entity})
        uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
        na_info = json.loads(self.agent.dstore.get(uri))
        na_info.update({"status": "defined"})
        self.__update_actual_store(entity_uuid, na_info)
        self.agent.logger.info('[ INFO ] Native Plugin - Defined BE uuid %s' % entity_uuid)
        return entity_uuid

    def undefineEntity(self, entity_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('[ INFO ] Native Plugin - Undefine BE uuid %s' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('[ ERRO ] Native Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.DEFINED:
            self.agent.logger.error('[ ERRO ] Native Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state",
                                                     str("Entity %s is not in DEFINED state" % entity_uuid))
        else:
            self.current_entities.pop(entity_uuid, None)
            self.agent.logger.info('[ DONE ] Native Plugin - Undefine BE uuid %s' % entity_uuid)
            return True

    def configureEntity(self, entity_uuid):

        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('[ INFO ] Native Plugin - Configure BE uuid %s' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('[ ERRO ] Native Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.DEFINED:
            self.agent.logger.error('[ ERRO ] Native Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in DEFINED state",
                                                     str("Entity %s is not in DEFINED state" % entity_uuid))
        else:


            self.agent.getOSPlugin().createFile(entity.outfile)
            entity.onConfigured()
            self.current_entities.update({entity_uuid: entity})
            uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
            na_info = json.loads(self.agent.dstore.get(uri))
            na_info.update({"status": "configured"})
            self.__update_actual_store(entity_uuid, na_info)
            self.agent.logger.info('[ DONE ] Native Plugin - Configure BE uuid %s' % entity_uuid)
            return True

    def cleanEntity(self, entity_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('[ INFO ] Native Plugin - Clean BE uuid %s' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('[ ERRO ] Native Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.CONFIGURED:
            self.agent.logger.error('[ ERRO ] Native Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in CONFIGURED state",
                                                     str("Entity %s is not in CONFIGURED state" % entity_uuid))
        else:

            self.agent.getOSPlugin().removeFile(entity.outfile)
            entity.onClean()
            self.current_entities.update({entity_uuid: entity})

            uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
            na_info = json.loads(self.agent.dstore.get(uri))
            na_info.update({"status": "cleaned"})
            self.__update_actual_store(entity_uuid, na_info)
            self.agent.logger.info('[ DONE ] Native Plugin - Clean BE uuid %s' % entity_uuid)
            return True

    def runEntity(self, entity_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('[ INFO ] Native Plugin - Starting BE uuid %s' % entity_uuid)
        entity = self.current_entities.get(entity_uuid,None)
        if entity is None:
            self.agent.logger.error('[ ERRO ] Native Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.CONFIGURED:
            self.agent.logger.error('[ ERRO ] Native Plugin - Entity state is wrong, or transition not allowed')
            raise StateTransitionNotAllowedException("Entity is not in CONFIGURED state",
                                                     str("Entity %s is not in CONFIGURED state" % entity_uuid))
        else:

            cmd = str("%s %s" % (entity.command, ' '.join(str(x) for x in entity.args)))
            process = self.__execute_command(cmd, entity.outfile)
            entity.onStart(process.pid, process)
            self.current_entities.update({entity_uuid: entity})
            uri = str('%s/%s/%s' % (self.agent.dhome, self.HOME, entity_uuid))
            na_info = json.loads(self.agent.dstore.get(uri))
            na_info.update({"status": "run"})
            self.__update_actual_store(entity_uuid, na_info)
            self.agent.logger.info('[ DONE ] Native Plugin - Runnign BE uuid %s' % entity_uuid)
            return True

    def stopEntity(self, entity_uuid):
        if type(entity_uuid) == dict:
            entity_uuid = entity_uuid.get('entity_uuid')
        self.agent.logger.info('[ INFO ] Native Plugin - Stop BE uuid %s' % entity_uuid)
        entity = self.current_entities.get(entity_uuid, None)
        if entity is None:
            self.agent.logger.error('[ ERRO ] Native Plugin - Entity not exists')
            raise EntityNotExistingException("Enitity not existing",
                                             str("Entity %s not in runtime %s" % (entity_uuid, self.uuid)))
        elif entity.getState() != State.RUNNING:
            self.agent.logger.error('[ ERRO ] Native Plugin - Entity state is wrong, or transition not allowed')
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
            self.agent.logger.info('[ DONE ] Native Plugin - Stopped BE uuid %s' % entity_uuid)
            return True

    def pauseEntity(self, entity_uuid):
        self.agent.logger.warning('[ WARN ] Native Plugin - Cannot pause a BE')
        return False

    def resumeEntity(self, entity_uuid):
        self.agent.logger.warning('[ WARN ] Native Plugin - Cannot resume a BE')
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
        self.agent.logger.info('[ INFO ] Native Plugin - React to to URI: %s Value: %s Version: %s' % (uri, value, v))
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





