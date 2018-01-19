import sys
import os
from fog05.interfaces.Plugin import Plugin


class MonitoringPlugin(Plugin):

    def __init__(self, version, plugin_uuid=None):
        super(MonitoringPlugin, self).__init__(version, plugin_uuid)
        self.name=''

    def start_monitoring(self):
        '''
        start the runtime
        :return: runtime pid or runtime uuid?
        '''
        raise NotImplementedError('This is and interface!')

    def stop_monitoring(self):
        '''
        stop this runtime
        '''
        raise NotImplementedError('This is and interface!')


