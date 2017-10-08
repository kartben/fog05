from interfaces.Store import *

class DController (Controller):

    def __init__(self, store):
        self.__store = store
        self.init_dds_entities(store)
        


    def init_dds_entities(self, store):
        self.home_writer = None
        self.home_dwriter = None
        self.home_pwriter = None

        self.home_reader = None
        self.home_dreader = None
        self.home_preader = None

        self.root_writer = None
        self.root_dwriter = None
        self.root_pwriter = None

        self.info_writer = None
        self.info_reader = None


