from Plugin import Plugin


class RuntimePlugin(Plugin):

    def __init__(self):
        self.pid=-1
        self.uuid="0"
        self.currentRunningEntities={}
        raise NotImplementedError("This is and interface!")


    def startRuntime(self):
        raise NotImplementedError("This is and interface!")

    def stopRuntime(self):
        raise NotImplementedError("This is and interface!")

    def launchEntity(self,*args):
        raise NotImplementedError("This is and interface!")

    def stopEntity(self,entityID):
        raise NotImplementedError("This is and interface!")

    def getEntities(self):
        raise NotImplementedError("This is and interface!")

    def migrateEntity(self,entityID):
        raise NotImplementedError("This is and interface!")

    def beforeMigrateEntityActions(self,entityID):
        raise NotImplementedError("This is and interface!")

    def afterMigrateEntityActions(self,entityID):
        raise NotImplementedError("This is and interface!")

    def scaleEntity(self,entityID):
        raise NotImplementedError("This is and interface!")

    def pauseEntity(self,entityID):
        raise NotImplementedError("This is and interface!")
    
    def resumeEntity(self,entityID):
        raise NotImplementedError("This is and interface!")

    def configureEntity(self,entityID):
        raise NotImplementedError("This is and interface!")

    def cleanEntity(self,entityID):
        raise NotImplementedError("This is and interface!")

