import sys
import os
from fog05.interfaces.Plugin import Plugin


class RuntimePlugin(Plugin):

    def __init__(self, version):
        super(RuntimePlugin, self).__init__(version)
        self.pid=-1
        self.uuid="0"
        self.name=""
        self.current_entities={}

    def startRuntime(self):
        """
        start the runtime
        :return: runtime pid or runtime uuid?
        """
        raise NotImplementedError("This is and interface!")

    def stopRuntime(self):
        """
        stop this runtime
        """
        raise NotImplementedError("This is and interface!")

    def getEntities(self):
        raise NotImplementedError("This is and interface!")

    def defineEntity(self, *args, **kwargs):
        """
        Define entity from args of from manifest file passed within parameters
        return the entity uuid
        :args: dict
        :return: String
        """

        raise NotImplementedError("This is and interface!")

    def undefineEntity(self,enitity_uuid):
        """
        Undefine the entity identified by entity_uuid
        if the entity state do not allow transition to UNDEFINED
        should throw an exception

        :entity_uuid: String
        :return: bool

        """
        raise NotImplementedError("This is and interface!")

    def runEntity(self, enitity_uuid):
        """
        Start the entity identified by entity_uuid
        if the entity state do not allow transition to RUN (eg is non CONFIGURED)
        should throw an exception

        :entity_uuid: String
        :return: bool

        """
        raise NotImplementedError("This is and interface!")

    def stopEntity(self, enitity_uuid):
        """
        Stop the entity identified by entity_uuid
        if the entity state do not allow transition to CONFIGURED (in this case is not in RUNNING)
        should throw an exception

        :entity_uuid: String
        :return: bool

        """
        raise NotImplementedError("This is and interface!")

    def migrateEntity(self, entity_uuid, dst=False):
        """
        Migrate the entity identified by entity_uuid to the new FogNode identified by fognode_uuid
        The migration depend to the nature of the entity (native app, µSvc, VM, Container)
        if the entity state do not allow transition to MIGRATE (eg a native app can't be migrated)
        should throw an exception
        if the destination node can't handle the migration an exception should be throwed

        To help migration should use the two methods:

        - beforeMigrateEntityActions()
        - afterMigrateEntiryActions()

        After the migration the entity on the source node has to be undefined
        the one on the destination node has to be in RUNNING


        :entity_uuid: String
        :fognode_uuid: String
        :return: bool

        """

        raise NotImplementedError("This is and interface!")

    def beforeMigrateEntityActions(self, entity_uuid, dst=False):
        """
        Action to be taken before a migration
        eg. copy disks of vms, save state of µSvc

        :entity_uuid: String
        :return: bool

        """

        raise NotImplementedError("This is and interface!")

    def afterMigrateEntityActions(self, entity_uuid, dst=False):

        """
        Action to be taken after a migration
        eg. delete disks of vms, delete state of µSvc, undefine entity

        :entity_uuid: String
        :return: bool

        """

        raise NotImplementedError("This is and interface!")

    def scaleEntity(self, entity_uuid):
        """
        Scale an entity
        eg. give more cpu/ram/disk, maybe passed by parameter the new scale value?

        if the entity state do not allow transition to SCALE (in this case is not in RUNNING)
        should throw an exception

        :entity_uuid: String
        :return: bool


        """
        raise NotImplementedError("This is and interface!")

    def pauseEntity(self, entity_uuid):
        """
        Pause an entity

        if the entity state do not allow transition to PAUSED (in this case is not in RUNNING)
        should throw an exception

        :entity_uuid: String
        :return: bool


        """
        raise NotImplementedError("This is and interface!")
    
    def resumeEntity(self, entity_uuid):
        """
        Resume an entity

        if the entity state do not allow transition to RUNNING (in this case is not in PAUSED)
        should throw an exception

        :entity_uuid: String
        :return: bool


        """
        raise NotImplementedError("This is and interface!")

    def configureEntity(self, entity_uuid):
        """
        Configure an entity

        if the entity state do not allow transition to CONFIGURED (in this case is not in DEFINED)
        should throw an exception

        :entity_uuid: String
        :return: bool


        """
        raise NotImplementedError("This is and interface!")

    def cleanEntity(self, entity_uuid):
        """
        Clean an entity

        if the entity state do not allow transition to DEFINED (in this case is not in CONFIGURED)
        should throw an exception

        :entity_uuid: String
        :return: bool


        """
        raise NotImplementedError("This is and interface!")

class EntityNotExistingException(Exception):
    def __init__(self, message, errors):

        super(EntityNotExistingException, self).__init__(message)
        self.errors = errors

class MigrationNotPossibleException(Exception):
    def __init__(self, message, errors):

        super(MigrationNotPossibleException, self).__init__(message)
        self.errors = errors

class MigrationNotAllowedException(Exception):
    def __init__(self, message, errors):

        super(MigrationNotAllowedException, self).__init__(message)
        self.errors = errors

class StateTransitionNotAllowedException(Exception):
    def __init__(self, message, errors):

        super(StateTransitionNotAllowedException, self).__init__(message)
        self.errors = errors