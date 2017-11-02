from interfaces.Agent import Agent
from PluginLoader import PluginLoader
import uuid
import sys
from DStore import *
#from RedisLocalCache import RedisCache
import json
#import networkx as nx
import re
import time
import logging


class FosAgent(Agent):

    def __init__(self):
        self.__PLUINGDIR = './plugins'
        self.LOGFILE = str('fosagent_log_%d.log' % int(time.time()))
        # Enable logging
        logging.basicConfig(filename=self.LOGFILE, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.logger.info('[ INFO ] FosAgent Starting...')
        self.pl = PluginLoader(self.__PLUINGDIR)
        self.pl.getPlugins()
        self.__osPlugin = None
        self.__rtPlugins = {}
        self.__nwPlugins = {}
        self.logger.info('[ INIT ] Loading OS Plugin...')
        self.__load_os_plugin()
        self.logger.info('[ DONE ] Loading OS Plugin...')
        super(FosAgent, self).__init__(self.__osPlugin.getUUID())
        sid = str(self.uuid)

        # Desidered Store. containing the desidered state
        self.droot = "dfos://<sys-id>"
        self.dhome = str("%s/%s" % (self.droot,sid))
        self.logger.info('[ INIT ] Creating Desidered State Store ROOT: %s HOME:%d' % (self.droot, self.dhome))
        self.dstore = DStore(sid, self.droot, self.dhome, 1024)
        self.logger.info('[ DONE ] Creating Desidered State Store')

        # Actual Store, containing the Actual State
        self.aroot = "afos://<sys-id>"
        self.ahome = str("%s/%s" % (self.aroot, sid))
        self.logger.info('[ INIT ] Creating Actual State Store ROOT: %s HOME:%d' % (self.aroot, self.ahome))
        self.astore = DStore(sid, self.aroot, self.ahome, 1024)
        self.logger.info('[ DONE ] Creating Actual State Store')

        self.logger.info('[ INIT ] Populating Actual Store with data from OS Plugin')
        val = {'status': 'add', 'version': self.__osPlugin.version, 'description': 'linux plugin', 'plugin': ''}
        uri = str('%s/plugins/%s/%s' % (self.ahome, self.__osPlugin.name, self.__osPlugin.uuid))
        self.astore.put(uri, json.dumps(val))

        val = {'plugins': [{'name': 'linux', 'version': self.__osPlugin.version, 'uuid': str(self.__osPlugin.uuid),
                           'type': 'os'}]}
        uri = str('%s/plugins' % self.ahome)
        self.astore.put(uri, json.dumps(val))

        val = {'plugins': []}
        uri = str('%s/plugins' % self.dhome)
        self.dstore.put(uri, json.dumps(val))

        self.__populate_node_information()
        self.logger.info('[ DONE ] Populating Actual Store with data from OS Plugin')

    def __load_os_plugin(self):
        platform = sys.platform
        if platform == 'linux':
            self.logger.info('[ INFO ] fosAgent running on GNU\Linux')
            os = self.pl.locatePlugin('linux')
            if os is not None:
                os = self.pl.loadPlugin(os)
                self.__osPlugin = os.run()
            else:
                self.logger.error('[ ERRO ] Error on Loading GNU\Linux plugin!!!')
                raise RuntimeError("Error on loading OS Plugin")
        elif platform == 'darwin':
            self.logger.info('[ INFO ] fosAgent running on macOS')
            self.logger.error('[ ERRO ] Mac plugin not yet implemented...')
            raise RuntimeError("Mac plugin not yet implemented...")
        elif platform == 'windows':
            self.logger.info('[ INFO ] fosAgent running on Windows')
            self.logger.error('[ ERRO ] Windows plugin not yet implemented...')
            raise RuntimeError("Windows plugin not yet implemented...")
        else:
            self.logger.error('[ ERRO ] Platform %s not compatible!!!!' % platform)
            raise RuntimeError("Platform not compatible")

    def getOSPlugin(self):
        return self.__osPlugin

    def __load_runtime_plugin(self, plugin_name):
        self.logger.info('[ INFO ] Loading a Runtime plugin: %s' % plugin_name)
        rt = self.pl.locatePlugin(plugin_name)
        if rt is not None:
            self.logger.info('[ INIT ] Loading a Runtime plugin: %s' % plugin_name)
            rt = self.pl.loadPlugin(rt)
            rt = rt.run(agent=self)
            self.__rtPlugins.update({rt.uuid: rt})
            val = {'version': rt.version, 'description': str('runtime %s' % rt.name), 'plugin': ''}
            uri = str('%s/plugins/%s/%s' % (self.ahome, rt.name, rt.uuid))
            self.astore.put(uri, json.dumps(val))

            val = {'plugins': [{'name': rt.name, 'version': rt.version, 'uuid': str(rt.uuid),
                                'type': 'runtime', 'status': 'loaded'}]}
            uri = str('%s/plugins' % self.ahome)
            self.astore.dput(uri, json.dumps(val))
            self.logger.info('[ DONE ] Loading a Runtime plugin: %s' % plugin_name)

            return rt
        else:
            self.logger.warning('[ WARN ] Runtime: %s plugin not found!' % plugin_name)
            return None

    def __load_network_plugin(self, plugin_name):
        self.logger.info('[ INFO ] Loading a Network plugin: %s' % plugin_name)
        net = self.pl.locatePlugin(plugin_name)
        if net is not None:
            self.logger.info('[ INIT ] Loading a Network plugin: %s' % plugin_name)
            net = self.pl.loadPlugin(net)
            net = net.run(agent=self)
            self.__rtPlugins.update({net.uuid: net})

            val = {'version': net.version, 'description': str('runtime %s' % net.name),
                   'plugin': ''}
            uri = str('%s/plugins/%s/%s' % (self.ahome, net.name, net.uuid))
            self.astore.put(uri, json.dumps(val))

            val = {'plugins': [{'name': net.name, 'version': net.version, 'uuid': str(net.uuid),
                                'type': 'network','status': 'loaded'}]}
            uri = str('%s/plugins' % self.ahome)
            self.astore.dput(uri, json.dumps(val))
            self.logger.info('[ DONE ] Loading a Network plugin: %s' % plugin_name)

            return net
        else:
            self.logger.warning('[ WARN ] Network: %s plugin not found!' % plugin_name)
            return None

    def __populate_node_information(self):

        node_info = {}
        node_info.update({'uuid': str(self.uuid)})
        node_info.update({'name': self.__osPlugin.getHostname()})
        node_info.update({'cpu': self.__osPlugin.getProcessorInformation()})
        node_info.update({'ram': self.__osPlugin.getMemoryInformation()})
        node_info.update({'disks': self.__osPlugin.getDisksInformation()})
        node_info.update({'network': self.__osPlugin.getNetworkInformations()})

        uri = str('%s/' % self.ahome)
        self.astore.put(uri, json.dumps(node_info))

    def __react_to_cache(self, uri, value, v):
        print ("###########################")
        print ("##### I'M an Observer #####")
        print ("## Key: %s" % uri)
        print ("## Value: %s" % value)
        print ("## V: %s" % v)
        print ("###########################")
        print ("###########################")

    def __react_to_plugins(self, uri, value, v):
        self.logger.info('[ INFO ] Received a plugin action on Desidered Store')
        value = json.loads(value)
        value = value.get('plugins')
        for v in value:
            if v.get('status') == 'add':
                name = v.get('name')
                load_method = self.__load_plugin_method_selection(v.get('type'))
                if load_method is not None:
                    load_method(name)
                else:
                    self.logger.warning('[ WARN ] Plugins of type %s are not yet supported...' % v.get('type'))

    def __load_plugin_method_selection(self, type):
        r = {
            'runtime': self.__load_runtime_plugin,
            'network': self.__load_network_plugin
        }
        return r.get(type, None)

    def __react_to_onboarding(self, uri, value, v):
        self.logger.info('[ INFO ] Received a onboard action on Desidered Store with URI:%s Value:%s Version:%s' % (uri, value, v))
        value = json.loads(value)
        application_uuid = uri.split('/')[-1]
        self.__application_onboarding(application_uuid, value)

    def __application_onboarding(self,application_uuid, value):
        self.logger.info('[ INFO ] Onboarding application with uuid: %s' % application_uuid)
        deploy_order_list = self.__resolve_dependencies(value.get('components', None))
        informations = {}
        '''
        With the ordered list of entities the agent should generate the graph of entities
        eg. using NetworkX lib and looking for loops, if it find a loop should fail the application
        onboarding, and signal in the proper uri.
        If no loop are detected then should start instantiate the components
        It's a MANO job to select the correct nodes, and selection should be based on proximity 
        After each deploy the agent should collect correct information for the deploy of components that need other
        components (eg. should retrive the ip address, and then pass in someway to others components)
        '''

        for c in deploy_order_list:
            search = [x for x in value.get('components') if x.get('name') == c]
            if len(search) > 0:
                component = search[0]
            else:
                self.logger.warning('[ WARN ] Could not find component in component list WTF?')
                raise AssertionError("Could not find component in component list WTF?")


            '''
            Should recover in some way the component manifest
            
            '''
            mf = self.__get_manifest(component.get('manifest'))
            '''
            from this manifest generate the correct json 
            '''
            t = mf.get('type')

            if t == "kvm":
                self.logger.info('[ INFO ] Component is a VM')
                kvm = self.__search_plugin_by_name('KVM')
                if kvm is None:
                    self.logger.error('[ ERRO ] KVM Plugin not loaded/found!!!')
                    return False

                '''
                Do stuffs... define, configure and run the vm
                get information about the deploy and save them
                eg. {'name':{ information }, 'name2':{}, .... }
                '''

                node_uuid = str(self.uuid) #@TODO: select deploy node in a smart way

                vm_uuid = mf.get("entity_description").get("uuid")

                entity_definition = {'status': 'define', 'name': component.get("name"), 'version': component.get(
                    'version'), 'entity_data': mf.get("entity_description")}
                json_data = json.dumps(entity_definition)

                self.logger.info('[ INFO ] Define VM')
                uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s' % (node_uuid, kvm.get('uuid'), vm_uuid))
                self.dstore.put(uri, json_data)

                while True:
                    self.logger.info('[ INFO ] Waiting VM to be DEFINED')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, kvm.get('uuid'), vm_uuid))
                    vm_info = json.loads(self.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "defined":
                        break
                self.logger.info('[ DONE ] VM DEFINED')

                self.logger.info('[ INFO ] Configure VM')
                uri = str(
                    'dfos://<sys-id>/%s/runtime/%s/entity/%s#status=configure' % (node_uuid, kvm.get('uuid'), vm_uuid))
                self.dstore.dput(uri)

                while True:
                    self.logger.info('[ INFO ] Waiting VM to be CONFIGURED')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, kvm.get('uuid'), vm_uuid))
                    vm_info = json.loads(self.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "configured":
                        break
                self.logger.info('[ DONE ] VM Configured')

                self.logger.info('[ INFO ] Staring VM')
                uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s#status=run' % (node_uuid, kvm.get('uuid'), vm_uuid))
                self.dstore.dput(uri)

                while True:
                    self.logger.info('[ INFO ] Waiting VM to be RUN')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, kvm.get('uuid'), vm_uuid))
                    vm_info = json.loads(self.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "run":
                        break

                self.logger.info('[ DONE ] VM Running on node:' % node_uuid)

            elif t == "container":
                self.logger.info('[ INFO ] Component is a Container')
            elif t == "native":
                self.logger.info('[ INFO ] Component is a Native Application')
                native = self.__search_plugin_by_name('native')
                if native is None:
                    self.logger.error('[ ERRO ] Native Application Plugin not loaded/found!!!')
                    return False

                node_uuid = str(self.uuid)  # @TODO: select deploy node in a smart way
                na_uuid = mf.get("entity_description").get("uuid")

                entity_definition = {'status': 'define', 'name': component.get("name"), 'version': component.get(
                    'version'), 'entity_data': mf.get("entity_description")}
                json_data = json.dumps(entity_definition)

                self.logger.info('[ INFO ] Define Native')
                uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s' % (node_uuid, native.get('uuid'), na_uuid))
                self.dstore.put(uri, json_data)

                while True:
                    self.logger.info('[ INFO ] Native to be DEFINED')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, native.get('uuid'), na_uuid))
                    vm_info = json.loads(self.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "defined":
                        break
                self.logger.info('[ DONE ] Native DEFINED')

                self.logger.info('[ INFO ] Configure Native')
                uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s#status=configure' %
                          (node_uuid, native.get('uuid'), na_uuid))
                self.dstore.dput(uri)

                while True:
                    self.logger.info('[ INFO ] Native to be CONFIGURED')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, native.get('uuid'), na_uuid))
                    vm_info = json.loads(self.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "configured":
                        break
                self.logger.info('[ DONE ] Native CONFIGURED')

                self.logger.info('[ INFO ] Starting Native')
                uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s#status=run' %
                          (node_uuid, native.get('uuid'), na_uuid))
                self.dstore.dput(uri)

                while True:
                    self.logger.info('[ INFO ] Native to be RUN')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, native.get('uuid'), na_uuid))
                    vm_info = json.loads(self.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "run":
                        break
                self.logger.info('[ DONE ] Native Running on node:' % node_uuid)

            elif t == "ros2":
                self.logger.info('[ INFO ] Component is a ROS2 Application')
                native = self.__search_plugin_by_name('ros2')
                if native is None:
                    self.logger.error('[ ERRO ] ROS2 Application Plugin not loaded/found!!!')
                    return False

                node_uuid = str(self.uuid)  # @TODO: select deploy node in a smart way
                na_uuid = mf.get("entity_description").get("uuid")

                entity_definition = {'status': 'define', 'name': component.get("name"), 'version': component.get(
                    'version'), 'entity_data': mf.get("entity_description")}
                json_data = json.dumps(entity_definition)

                self.logger.info('[ INFO ] Define ROS2')
                uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s' % (node_uuid, native.get('uuid'), na_uuid))
                self.dstore.put(uri, json_data)

                while True:
                    self.logger.info('[ INFO ] ROS2 to be DEFINED')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, native.get('uuid'), na_uuid))
                    vm_info = json.loads(self.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "defined":
                        break
                self.logger.info('[ DONE ] ROS2 DEFINED')

                self.logger.info('[ INFO ] Configure Native')
                uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s#status=configure' %
                          (node_uuid, native.get('uuid'), na_uuid))
                self.dstore.dput(uri)

                while True:
                    self.logger.info('[ INFO ] ROS2 to be CONFIGURED')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, native.get('uuid'), na_uuid))
                    vm_info = json.loads(self.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "configured":
                        break
                self.logger.info('[ DONE ] ROS2 CONFIGURED')

                self.logger.info('[ INFO ] Starting ROS2')
                uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s#status=run' %
                          (node_uuid, native.get('uuid'), na_uuid))
                self.dstore.dput(uri)

                while True:
                    self.logger.info('[ INFO ] ROS2 to be RUN')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, native.get('uuid'), na_uuid))
                    vm_info = json.loads(self.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "run":
                        break
                self.logger.info('[ DONE ] ROS2 Running on node:' % node_uuid)

            elif t == "usvc":
                self.logger.info('[ INFO ] Component is a Microservice')

            elif t == "application":
                self.logger.info('[ INFO ] Component is a Complex Application')
                self.__application_onboarding(mf.get("uuid"), mf.get("entity_description"))

            else:
                self.logger.error("Component type not recognized %s" % t)
                raise AssertionError("Component type not recognized %s" % t)

    def __resolve_dependencies(self, components):
        '''
        The return list contains component's name in the order that can be used to deploy
         @TODO: should use less cycle to do this job
        :rtype: list
        :param components: list like [{'name': 'c1', 'need': ['c2', 'c3']}, {'name': 'c2', 'need': ['c3']}, {'name': 'c3', 'need': ['c4']}, {'name': 'c4', 'need': []}, {'name': 'c5', 'need': []}]

        no_dependable_components -> list like [[{'name': 'c4', 'need': []}, {'name': 'c5', 'need': []}], [{'name': 'c3', 'need': []}], [{'name': 'c2', 'need': []}], [{'name': 'c1', 'need': []}], []]
        :return: list like ['c4', 'c5', 'c3', 'c2', 'c1']
        '''
        c = list(components)
        no_dependable_components = []
        for i in range(0, len(components)):
            no_dependable_components.append([x for x in c if len(x.get('need')) == 0])
            #print (no_dependable_components)
            c = [x for x in c if x not in no_dependable_components[i]]
            for y in c:
                n = y.get('need')
                n = [x for x in n if x not in [z.get('name') for z in no_dependable_components[i]]]
                y.update({"need": n})

        order = []
        for i in range(0, len(no_dependable_components)):
            n = [x.get('name') for x in no_dependable_components[i]]
            order.extend(n)
        return order

    def __get_manifest(self, manifest_path):
        return json.loads(self.dstore.get(manifest_path))

    def __search_plugin_by_name(self, name):
        uri = str('%s/plugins' % self.ahome)
        all_plugins = json.loads(self.astore.get(uri)).get('plugins')
        search = [x for x in all_plugins if name in x.get('name')]
        if len(search) == 0:
            return None
        else:
            return search[0]

    def main(self):


        uri = str('%s/onboard/*/' % self.dhome)
        self.dstore.observe(uri, self.__react_to_onboarding)
        self.logger.info('[ INFO ] fosAgent Observing for onboarding on: %s' % uri)

        uri = str('%s/*/' % self.dhome)
        self.dstore.observe(uri, self.__react_to_cache)
        self.logger.info('[ INFO ] fosAgent Observing home on: %s' % uri)

        uri = str('%s/plugins' % self.dhome)
        self.dstore.observe(uri, self.__react_to_plugins)
        self.logger.info('[ INFO ] fosAgent Observing plugins on: %s' % uri)

        self.logger.info('[ DONE ] fosAgent Up and Running')
        while True:
            time.sleep(100)







if __name__=='__main__':
    print(" _____            ___  ____\n|  ___|__   __ _ / _ \/ ___|\n| |_ / _ \ / _` | | | \___ \ \n|  _| (_) | (_| "
          "| |_| |___) |\n|_|  \___/ \__, |\___/|____/\n           |___/")
    print("\n\n##### OUTPUT TO LOGFILE #####\n\n")
    agent = FosAgent()
    agent.main()

