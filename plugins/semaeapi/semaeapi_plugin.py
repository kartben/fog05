import sys
import os
import uuid
import struct
import json
from fog05.interfaces.MonitoringPlugin import *
import psutil
import re
import subprocess
import threading
import time


class semaeapi(MonitoringPlugin):

    def __init__(self, name, version, agent, plugin_uuid):
        super(semaeapi, self).__init__(version, plugin_uuid)
        self.name = name
        self.agent = agent
        self.HOME = 'monitoring/{}'.format(self.uuid)
        self.UPDATE_FREQUENCY = 'update'
        self.STATUS = 'status'

        uri = '{}/{}/set/*'.format(self.agent.dhome, self.HOME)
        self.agent.dstore.observe(uri, self.__react_to_cache_eapi_monitoring)
        self.agent.logger.info('__init__()', ' SEMAEApi Plugin - Observing {}'.format(uri))

        self.available_api = {}
        self.__updating_thread = None
        self.__monitoring_active = False
        self.frequency = 30

        self.start_monitoring()

    def start_monitoring(self):

        if self.__monitoring_active:
            self.agent.logger.info('start_monitoring()', ' SEMAEApi Plugin - Monitoring already active...')
            return

        self.agent.logger.info('start_monitoring()', ' SEMAEApi Plugin - Scanning available eAPI')
        exp = r'(Sema[^ ]*)'
        res = self.__execute_sema_cli('semaeapi_tool')
        matches = re.findall(exp,res)
        if matches:
            for api in matches:
                self.available_api.update({api: []})
            for k in list(self.available_api.keys()):
                exp = r'(([0-9][0-9]|[0-9]).*)'
                cmd = 'semaeapi_tool -a {}'.format(k)
                res = self.__execute_sema_cli(cmd)
                v = self.available_api.get(k)
                m2 = re.findall(exp, res)
                for id in m2:
                    id = id[0]
                    id = id.split()
                    if len(id)>1:
                        v.append({'id': id[0], 'name': id[1]})
                self.available_api.update({k: v})

        self.agent.logger.info('start_monitoring()', ' SEMAEApi Plugin - Found {} eAPI'.format(len(matches)))
        self.__updating_thread = threading.Thread(target=self.__monitoring_thread)
        self.__monitoring_active = True
        self.__updating_thread.start()

        self.__update_actual_store(self.STATUS, {'monitoring': self.__monitoring_active})
        self.__update_actual_store(self.UPDATE_FREQUENCY, {'frequency': self.frequency})
        self.agent.logger.info('start_monitoring()', ' SEMAEApi Plugin - Monitoring started...')



    def stop_monitoring(self):
        if not self.__monitoring_active:
            self.agent.logger.info('start_monitoring()', ' SEMAEApi Plugin - Monitoring already stopped...')
            return
        self.__monitoring_active = False
        self.__update_actual_store(self.STATUS, {'monitoring': self.__monitoring_active})
        self.agent.logger.info('stop_monitoring()', 'SEMAEApi Plugin - Monitoring stopped...')
        self.available_api.clear()


    def __pop_actual_store(self, uri):
        #e = uri
        uri = str("{}/{}/{}".format(self.agent.ahome, self.HOME, uri))
        self.agent.astore.remove(uri)
        #uri = str("%s/%s/%s" % (self.agent.dhome, self.HOME, e))
        #self.agent.dstore.remove(uri)

    def __update_actual_store(self, uri, value):
        uri = '{}/{}/{}'.format(self.agent.ahome, self.HOME, uri)
        value = json.dumps(value)
        self.agent.astore.put(uri, value)

    def __monitoring_thread(self):
        while self.__monitoring_active:
            for k in list(self.available_api.keys()):
                if 'Set' not in k and 'Write' not in k:
                    v = self.available_api.get(k)
                    for api in v:
                        if isinstance(api, dict):
                            id = api.get('id')
                            name = api.get('name')
                            uri = '{}/{}'.format(k, name)
                            cmd = 'semaeapi_tool -a {} {}'.format(k, id)
                        else:
                            uri = '{}/'.format(k)
                            cmd = 'semaeapi_tool -a {}'.format(k)

                        res = self.__execute_sema_cli(cmd)
                        if 'get eapi information failed' in res:
                            status = 'error'
                        else:
                            status = 'ok'

                        value = res
                        val = {'status': status, 'value': value}
                        self.__update_actual_store(uri, val)
            time.sleep(self.frequency)





    def __react_to_cache_eapi_monitoring(self, key, value, v):
        self.agent.logger.info('__react_to_cache_eapi_monitoring()',
                               'SEMAEApi Plugin - React to to URI: {} Value: {} Version: {}'.format(key, value, v))
        if value is None and v is None:
            self.agent.logger.info('__react_to_cache_eapi_monitoring()', 'SEMAEApi Plugin - This is a remove for URI: {}'.format(key))
            self.agent.logger.info('__react_to_cache_eapi_monitoring()',  'Cannot remove a monitoring URI....')
        else:
            name = key.split('/')[-1]
            value = json.loads(value)
            if name == 'update':
                self.frequency = int(value.get('frequency'))
                self.__update_actual_store(self.UPDATE_FREQUENCY, {'frequency': self.frequency})
            if name == 'status':
                if bool(value.get('monitoring')) is False:
                    self.stop_monitoring()
                else:
                    self.start_monitoring()
            api = key.split(self.uuid)[1]
            if api.split('/')[1] in self.available_api.keys():
                cmd = api[1:].split('/')
                cmd = ' '.join(cmd)
                ret = self.__execute_sema_cli(cmd)
                if 'get eapi information failed' in ret:
                    status = 'error'
                else:
                    status = 'ok'
                val = {'status': status, 'value': ret}
                uri = api[1:]
                self.__update_actual_store(uri, ret)

            # TODO set actions...


    def __execute_sema_cli(self, cmd):
        cmd_splitted = cmd.split()
        p = psutil.Popen(cmd_splitted, stdout=subprocess.PIPE)
        p.wait()
        ret = ''
        for line in p.stdout:
            ret = ret+'{}'.format(line.decode())
        return ret
