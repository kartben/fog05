from Plugin import Plugin


class OSPlugin(Plugin):

    def __init__(self):
        raise NotImplementedError("This is and interface!")

    def executeCommand(self,command):
        raise NotImplementedError("This is and interface!")

    def installPackage(self,packages):
        raise NotImplementedError("This is and interface!")
    
    def storeFile(self,content,file_path,filename):
        raise NotImplementedError("This is and interface!")

    def readFile(self,file_path):
        raise NotImplementedError("This is and interface!")

    def getCPUID(self):
        raise NotImplementedError("This is and interface!")

    def getCPULevel(self):
        raise NotImplementedError("This is and interface!")

    def getMemoryLevel(self):
        raise NotImplementedError("This is and interface!")

    def getStorageLevel(self):
        raise NotImplementedError("This is and interface!")
    
    def getNetworkLevel(self):
        raise NotImplementedError("This is and interface!")

    def removePackage(self,packages):
        raise NotImplementedError("This is and interface!")

    def sendSignal(self,signal,pid):
        raise NotImplementedError("This is and interface!")

    def getPid(self,process):
        raise NotImplementedError("This is and interface!")

    def sendSigInt(self,pid):
        raise NotImplementedError("This is and interface!")

    def sendSigKill(self,pid):
        raise NotImplementedError("This is and interface!")