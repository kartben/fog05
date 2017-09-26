class DistribuitedCache():

    def __init__(self):
        raise NotImplementedError("This is and interface!")

    def allocateCache(self, size):
        raise NotImplementedError("This is and interface!")

    def deallocateCache(self, size):
        raise NotImplementedError("This is and interface!")

    def read(self, key):
        raise NotImplementedError("This is and interface!")

    def take(self, key):
        raise NotImplementedError("This is and interface!")
    
    def write(self, key, value):
        raise NotImplementedError("This is and interface!")
    
    def query(self, function):
        raise NotImplementedError("This is and interface!")

    def addContinuousQuery(self, function, listener):
        raise NotImplementedError("This is and interface!")

    def addMissingHandler(self, handler):
        raise NotImplementedError("This is and interface!")
    
    def addInsertHandler(self, handler):
        raise NotImplementedError("This is and interface!")
    
    def getIterator(self):
        raise NotImplementedError("This is and interface!")

    