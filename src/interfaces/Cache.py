class Observer(object):

    def onPut(self, uri, value):
        raise NotImplemented("Not yet...")

    # One of these for each operation on the cache...


class Controller(object):
    """
    Controls the cache, in the sense that automatically fills it with the 
    information coming from the network, e.g. from DDS.
     
    """

    def __init__(self, cache):
        self.cache = cache


    def start(self):
        """
            This method starts the controller and "connects" the cache to the rest of the system.

        """
        raise NotImplemented("Not yet...")

    def pause(self):
        """
            Pauses the execution of the controller. The incoming updates are not lost.
        """
        raise NotImplemented("Not yet...")

    def resume(self):
        """
            Resumes the execution of the controller and applies all pending changes received from the network.
        """
        raise NotImplemented("Not yet...")


    def stop(self):
        """
            Stops a controller and releases all resources used to receive/send data on the network.
        """

