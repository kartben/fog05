import sys
import os
sys.path.append(os.path.join(sys.path[0],'interfaces'))
from Entity import Entity

class LibVirtEntity(Entity):

    def __init__(self,name,uuid):
        self.uuid=uuid
        self.name=name

