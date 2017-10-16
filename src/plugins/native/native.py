import sys
import os
import uuid
import psutil
import json
sys.path.append(os.path.join(sys.path[0], 'interfaces'))
from States import State
from RuntimePlugin import *
from NativeEntity import NativeEntity



class Native(RuntimePlugin):

    def __init__(self, name, version, agent):
        super(Native, self).__init__(version)
        self.uuid = uuid.uuid4()
        self.name = name
        self.agent = agent
        self.startRuntime()

    def startRuntime(self):
        uri = str('fos://<sys-id>/%s/runtime/%s/entity/*' % (self.agent.uuid, self.uuid))
        print("KVM Listening on %s" % uri)
        self.agent.store.observe(uri, self.reactToCache)
        return self.uuid

    def stopRuntime(self):
        print ("Stopping native runtime...")
        return True

    def defineEntity(self, *args, **kwargs):

        if len(kwargs) > 0:
            entity_uuid = kwargs.get('entity_uuid')
            out_file = str("/opt/fos/logs/native_%s.log" % entity_uuid)
            entity = NativeEntity(entity_uuid, kwargs.get('name'), kwargs.get('command'), kwargs.get('args'), out_file)
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
            self.currentEntities.pop(entity_uuid, None)
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

            create_file = str("touch %s" % entity.outfile)
            self.agent.getOSPlugin().executeCommand(create_file)
            entity.onConfigured()
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
            rm_cmd = str("rm -f %s" % entity.outfile)
            self.agent.getOSPlugin().executeCommand(rm_cmd)
            entity.onClean()
            self.currentEntities.update({entity_uuid: entity})
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

            cmd = str("%s %s" % (entity.command, ' '.join(str(x) for x in entity.args)))
            process = self.execute_command(cmd, entity.outfile)
            entity.onStart(process.pid, process)
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
            p = entity.process
            p.terminate()
            entity.onStop()
            self.currentEntities.update({entity_uuid: entity})
            return True

    def pauseEntity(self, entity_uuid):
        print("Can't pause a native application")
        return False

    def resumeEntity(self, entity_uuid):
        print("Can't resume a native application")
        return False

    def execute_command(self, command, out_file):
        f = open(out_file, 'w')
        cmd_splitted = command.split()
        p = psutil.Popen(cmd_splitted, stdout=f)
        return p

    def reactToCache(self, uri, value, v):
        print("Native on React \nURI:%s\nValue:%s\nVersion:%s" % (uri, value, v))
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
                react_func(entity_data)

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





