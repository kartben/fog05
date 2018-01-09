from fog05.interfaces.Agent import Agent
from fog05.PluginLoader import PluginLoader
from fog05.DLogger import DLogger
import sys
from fog05.DStore import *
import json
#import networkx as nx
import time
import logging
import signal
import traceback


class FosAgent(Agent):

    def __init__(self, debug=True, plugins_path=None):
        print(" _____            ____   ____\n"
              "|  ___|__   __ _ / __ \ | ___|\n"
              "| |_ / _ \ / _` | | /| ||___ \ \n"
              "|  _| (_) | (_| | |/_| | ___) |\n"
              "|_|  \___/ \__, |\____/ |____/ \n"
              "           |___/ \n")

        #if not debug:
            #self.LOGFILE = str('fosagent_log_%d.log' % int(time.time()))
            #logging.basicConfig(filename=self.LOGFILE,
            #                    format='[%(asctime)s] - %(name)s - [%(levelname)s] > %(message)s',
            #                    level=logging.INFO)
        #else:
        #    self.LOGFILE = "stdout"
        #    logging.basicConfig(format='[%(asctime)s] - %(name)s - [%(levelname)s] > %(message)s',
        #                        level=logging.INFO)
        # Enable logging

        self.logger = DLogger(debug_flag=debug) #logging.getLogger(__name__)
        print("\n\n##### OUTPUT TO LOGFILE #####\n\n")
        #print("\n\n##### LOGFILE %s ####\n\n" % self.LOGFILE)
        self.logger.info('__init__()', 'FosAgent Starting...')

        if plugins_path is None:
            self.__PLUGINDIR = './plugins'
        else:
            self.__PLUGINDIR = plugins_path

        try:

            self.logger.info('__init__()', 'Plugins Dir: %s' % self.__PLUGINDIR)
            self.pl = PluginLoader(self.__PLUGINDIR)
            self.pl.getPlugins()
            self.__osPlugin = None
            self.__rtPlugins = {}
            self.__nwPlugins = {}
            self.logger.info('__init__()', '[ INIT ] Loading OS Plugin...')
            self.__load_os_plugin()
            self.logger.info('__init__()', '[ DONE ] Loading OS Plugin...')
            super(FosAgent, self).__init__(self.__osPlugin.getUUID())
            sid = str(self.uuid)

            self.base_path = self.__osPlugin.get_base_path()

            # Desidered Store. containing the desidered state
            self.droot = "dfos://<sys-id>"
            self.dhome = str("%s/%s" % (self.droot, sid))
            self.logger.info('__init__()', '[ INIT ] Creating Desidered State Store ROOT: %s HOME: %s' % (self.droot,
                                                                                                          self.dhome))
            self.dstore = DStore(sid, self.droot, self.dhome, 1024)
            self.logger.info('__init__()', '[ DONE ] Creating Desidered State Store')

            # Actual Store, containing the Actual State
            self.aroot = "afos://<sys-id>"
            self.ahome = str("%s/%s" % (self.aroot, sid))
            self.logger.info('__init__()', '[ INIT ] Creating Actual State Store ROOT: %s HOME: %s' % (self.aroot,
                                                                                                       self.ahome))
            self.astore = DStore(sid, self.aroot, self.ahome, 1024)
            self.logger.info('__init__()', '[ DONE ] Creating Actual State Store')

            self.logger.info('__init__()', '[ INIT ] Populating Actual Store with data from OS Plugin')
            val = {'version': self.__osPlugin.version, 'description': '{0} plugin'.format(self.__osPlugin.name)}
            uri = str('%s/plugins/%s/%s' % (self.ahome, self.__osPlugin.name, self.__osPlugin.uuid))
            self.astore.put(uri, json.dumps(val))

            val = {'plugins': [{'name': self.__osPlugin.name, 'version': self.__osPlugin.version, 'uuid': str(
                self.__osPlugin.uuid), 'type': 'os', 'status': 'loaded'}]}
            uri = str('%s/plugins' % self.ahome)
            self.astore.put(uri, json.dumps(val))

            val = {'plugins': []}
            uri = str('%s/plugins' % self.dhome)
            self.dstore.put(uri, json.dumps(val))

            self.__populate_node_information()
            self.logger.info('__init__()', '[ DONE ] Populating Actual Store with data from OS Plugin')
        except FileNotFoundError as fne:
            self.logger.error('__init__()', "File Not Found Aborting %s " % fne.strerror)
            exit(-1)
        except Error as e:
            self.logger.error('__init__()', "Something trouble happen %s " % e.strerror)
            exit(-1)


    def __load_os_plugin(self):
        platform = sys.platform
        if platform == 'linux':
            self.logger.info('__init__()', 'fosAgent running on GNU\Linux')
            os = self.pl.locatePlugin('linux')
            if os is not None:
                os = self.pl.loadPlugin(os)
                self.__osPlugin = os.run(agent=self)
            else:
                self.logger.error('__load_os_plugin()', 'Error on Loading GNU\Linux plugin!!!')
                raise RuntimeError("Error on loading OS Plugin")
        elif platform == 'darwin':
            self.logger.info('__load_os_plugin()', 'fosAgent running on macOS')
            self.logger.error('__load_os_plugin()', ' Mac plugin not yet implemented...')
            raise RuntimeError("Mac plugin not yet implemented...")
        elif platform in ['windows', 'Windows', 'win32']:
            os = self.pl.locatePlugin('windows')
            if os is not None:
                os = self.pl.loadPlugin(os)
                self.__osPlugin = os.run(agent=self)
            else:
                self.logger.error('__load_os_plugin()', 'Error on Loading GNU\Linux plugin!!!')
                raise RuntimeError("Error on loading OS Plugin")
        else:
            self.logger.error('__load_os_plugin()', 'Platform %s not compatible!!!!' % platform)
            raise RuntimeError('__load_os_plugin()', "Platform not compatible")

    def getOSPlugin(self):
        return self.__osPlugin

    def getNetworkPlugin(self, cnetwork_uuid):
        if cnetwork_uuid is None:
            return self.__nwPlugins
        else:
            return self.__nwPlugins.get(cnetwork_uuid)

    def __load_runtime_plugin(self, plugin_name, plugin_uuid):
        self.logger.info('__load_runtime_plugin()', 'Loading a Runtime plugin: %s' % plugin_name)
        rt = self.pl.locatePlugin(plugin_name)
        if rt is not None:
            self.logger.info('__load_runtime_plugin()', '[ INIT ] Loading a Runtime plugin: %s' % plugin_name)
            rt = self.pl.loadPlugin(rt)
            rt = rt.run(agent=self, uuid=plugin_uuid)
            self.__rtPlugins.update({rt.uuid: rt})
            val = {'version': rt.version, 'description': str('runtime %s' % rt.name), 'plugin': ''}
            uri = str('%s/plugins/%s/%s' % (self.ahome, rt.name, rt.uuid))
            self.astore.put(uri, json.dumps(val))

            val = {'plugins': [{'name': rt.name, 'version': rt.version, 'uuid': str(rt.uuid),
                                'type': 'runtime', 'status': 'loaded'}]}
            uri = str('%s/plugins' % self.ahome)
            self.astore.dput(uri, json.dumps(val))
            self.logger.info('__load_runtime_plugin()', '[ DONE ] Loading a Runtime plugin: %s' % plugin_name)

            return rt
        else:
            self.logger.warning('__load_runtime_plugin()', '[ WARN ] Runtime: %s plugin not found!' % plugin_name)
            return None

    def __load_network_plugin(self, plugin_name, plugin_uuid):
        self.logger.info('__load_network_plugin()', 'Loading a Network plugin: %s' % plugin_name)
        net = self.pl.locatePlugin(plugin_name)
        if net is not None:
            self.logger.info('__load_network_plugin()', '[ INIT ] Loading a Network plugin: %s' % plugin_name)
            net = self.pl.loadPlugin(net)
            net = net.run(agent=self, uuid=plugin_uuid)
            self.__nwPlugins.update({net.uuid: net})

            val = {'version': net.version, 'description': str('runtime %s' % net.name),
                   'plugin': ''}
            uri = str('%s/plugins/%s/%s' % (self.ahome, net.name, net.uuid))
            self.astore.put(uri, json.dumps(val))

            val = {'plugins': [{'name': net.name, 'version': net.version, 'uuid': str(net.uuid),
                                'type': 'network', 'status': 'loaded'}]}
            uri = str('%s/plugins' % self.ahome)
            self.astore.dput(uri, json.dumps(val))
            self.logger.info('__load_network_plugin()', '[ DONE ] Loading a Network plugin: %s' % plugin_name)

            return net
        else:
            self.logger.warning('__load_network_plugin()', '[ WARN ] Network: %s plugin not found!' % plugin_name)
            return None

    def __populate_node_information(self):

        node_info = {}
        node_info.update({'uuid': str(self.uuid)})
        node_info.update({'name': self.__osPlugin.getHostname()})
        node_info.update({'os': self.__osPlugin.name})
        node_info.update({'cpu': self.__osPlugin.getProcessorInformation()})
        node_info.update({'ram': self.__osPlugin.getMemoryInformation()})
        node_info.update({'disks': self.__osPlugin.getDisksInformation()})
        node_info.update({'network': self.__osPlugin.getNetworkInformations()})
        node_info.update({'io': self.__osPlugin.getIOInformations()})
        node_info.update({'accelerator': self.__osPlugin.getAcceleratorsInformations()})

        uri = str('%s/' % self.ahome)
        self.astore.put(uri, json.dumps(node_info))

    def __react_to_cache(self, uri, value, v):
        print("###########################")
        print("##### I'M an Observer #####")
        print("## Key: %s" % uri)
        print("## Value: %s" % value)
        print("## V: %s" % v)
        print("###########################")
        print("###########################")

    def __react_to_plugins(self, uri, value, v):
        self.logger.info('__react_to_plugins()', ' Received a plugin action on Desidered Store URI: %s Value: %s '
                         'Version: %s' % (uri, value, v))
        value = json.loads(value)
        value = value.get('plugins')
        for v in value:
            uri = str('%s/plugins' % self.ahome)
            all_plugins = json.loads(self.astore.get(uri))
            s = [x for x in all_plugins.get('plugins') if v.get('name') in x.get('name')]
            if v.get('status') == 'add' and len(s) == 0:
                name = v.get('name')
                plugin_uuid = v.get('uuid')
                load_method = self.__load_plugin_method_selection(v.get('type'))
                if load_method is not None:
                    load_method(name, plugin_uuid)
                else:
                    if len(s) != 0:
                        self.logger.warning('__react_to_plugins()', '[ WARN ] Plugins of type %s are not yet '
                                            'supported...' % v.get('type'))
                    else:
                        self.logger.warning('__react_to_plugins()', '[ WARN ] Plugin already loaded')

    def __load_plugin_method_selection(self, type):
        r = {
            'runtime': self.__load_runtime_plugin,
            'network': self.__load_network_plugin
        }
        return r.get(type, None)

    def __react_to_onboarding(self, uri, value, v):
        self.logger.info('__react_to_onboarding()', 'Received a onboard action on Desidered Store with URI:%s '
                         'Value:%s Version:%s' % (uri, value, v))
        value = json.loads(value)
        application_uuid = uri.split('/')[-1]
        self.__application_onboarding(application_uuid, value)

    def __application_onboarding(self, application_uuid, value):
        self.logger.info('__application_onboarding()', ' Onboarding application with uuid: %s' % application_uuid)
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
                self.logger.warning('__application_onboarding()', '[ WARN ] Could not find component in component list WTF?')
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
                self.logger.info(' Component is a VM')
                kvm = self.__search_plugin_by_name('KVM')
                if kvm is None:
                    self.logger.error('__application_onboarding()', '[ ERRO ] KVM Plugin not loaded/found!!!')
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

                self.logger.info('__application_onboarding()', ' Define VM')
                uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s' % (node_uuid, kvm.get('uuid'), vm_uuid))
                self.dstore.put(uri, json_data)

                while True:
                    self.logger.info('__application_onboarding()', ' Waiting VM to be DEFINED')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, kvm.get('uuid'), vm_uuid))
                    vm_info = json.loads(self.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "defined":
                        break
                self.logger.info('__application_onboarding()', '[ DONE ] VM DEFINED')

                self.logger.info('__application_onboarding()', 'Configure VM')
                uri = str(
                    'dfos://<sys-id>/%s/runtime/%s/entity/%s#status=configure' % (node_uuid, kvm.get('uuid'), vm_uuid))
                self.dstore.dput(uri)

                while True:
                    self.logger.info('__application_onboarding()', 'Waiting VM to be CONFIGURED')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, kvm.get('uuid'), vm_uuid))
                    vm_info = json.loads(self.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "configured":
                        break
                self.logger.info('__application_onboarding()', '[ DONE ] VM Configured')

                self.logger.info('__application_onboarding()', 'Staring VM')
                uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s#status=run' % (node_uuid, kvm.get('uuid'), vm_uuid))
                self.dstore.dput(uri)

                while True:
                    self.logger.info('Waiting VM to be RUN')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, kvm.get('uuid'), vm_uuid))
                    vm_info = json.loads(self.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "run":
                        break

                self.logger.info('__application_onboarding()', '[ DONE ] VM Running on node: %s' % node_uuid)

            elif t == "container":
                self.logger.info('__application_onboarding()', 'Component is a Container')
            elif t == "native":
                self.logger.info('__application_onboarding()', 'Component is a Native Application')
                native = self.__search_plugin_by_name('native')
                if native is None:
                    self.logger.error('__application_onboarding()', '[ ERRO ] Native Application Plugin not loaded/found!!!')
                    return False

                node_uuid = str(self.uuid)  # @TODO: select deploy node in a smart way
                na_uuid = mf.get("entity_description").get("uuid")

                entity_definition = {'status': 'define', 'name': component.get("name"), 'version': component.get(
                    'version'), 'entity_data': mf.get("entity_description")}
                json_data = json.dumps(entity_definition)

                self.logger.info('__application_onboarding()', 'Define Native')
                uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s' % (node_uuid, native.get('uuid'), na_uuid))
                self.dstore.put(uri, json_data)

                while True:
                    self.logger.info('__application_onboarding()', 'Native to be DEFINED')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, native.get('uuid'), na_uuid))
                    vm_info = json.loads(self.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "defined":
                        break
                self.logger.info('__application_onboarding()', '[ DONE ] Native DEFINED')

                self.logger.info('__application_onboarding()', ' Configure Native')
                uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s#status=configure' %
                          (node_uuid, native.get('uuid'), na_uuid))
                self.dstore.dput(uri)

                while True:
                    self.logger.info('__application_onboarding()', 'Native to be CONFIGURED')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, native.get('uuid'), na_uuid))
                    vm_info = json.loads(self.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "configured":
                        break
                self.logger.info('__application_onboarding()', '[ DONE ] Native CONFIGURED')

                self.logger.info('__application_onboarding()', 'Starting Native')
                uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s#status=run' %
                          (node_uuid, native.get('uuid'), na_uuid))
                self.dstore.dput(uri)

                while True:
                    self.logger.info('__application_onboarding()', 'Native to be RUN')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, native.get('uuid'), na_uuid))
                    vm_info = json.loads(self.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "run":
                        break
                self.logger.info('__application_onboarding()', '[ DONE ] Native Running on node: %s' % node_uuid)

            elif t == "ros2":
                self.logger.info('Component is a ROS2 Application')
                native = self.__search_plugin_by_name('ros2')
                if native is None:
                    self.logger.error('__application_onboarding()', '[ ERRO ] ROS2 Application Plugin not loaded/found!!!')
                    return False

                node_uuid = str(self.uuid)  # @TODO: select deploy node in a smart way
                na_uuid = mf.get("entity_description").get("uuid")

                entity_definition = {'status': 'define', 'name': component.get("name"), 'version': component.get(
                    'version'), 'entity_data': mf.get("entity_description")}
                json_data = json.dumps(entity_definition)

                self.logger.info('__application_onboarding()', 'Define ROS2')
                uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s' % (node_uuid, native.get('uuid'), na_uuid))
                self.dstore.put(uri, json_data)

                while True:
                    self.logger.info('__application_onboarding()', 'ROS2 to be DEFINED')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, native.get('uuid'), na_uuid))
                    vm_info = json.loads(self.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "defined":
                        break
                self.logger.info('__application_onboarding()', '[ DONE ] ROS2 DEFINED')

                self.logger.info('__application_onboarding()', 'Configure Native')
                uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s#status=configure' %
                          (node_uuid, native.get('uuid'), na_uuid))
                self.dstore.dput(uri)

                while True:
                    self.logger.info('__application_onboarding()', 'ROS2 to be CONFIGURED')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, native.get('uuid'), na_uuid))
                    vm_info = json.loads(self.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "configured":
                        break
                self.logger.info('__application_onboarding()', '[ DONE ] ROS2 CONFIGURED')

                self.logger.info('__application_onboarding()', 'Starting ROS2')
                uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s#status=run' %
                          (node_uuid, native.get('uuid'), na_uuid))
                self.dstore.dput(uri)

                while True:
                    self.logger.info('__application_onboarding()', 'ROS2 to be RUN')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, native.get('uuid'), na_uuid))
                    vm_info = json.loads(self.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "run":
                        break
                self.logger.info('__application_onboarding()', '[ DONE ] ROS2 Running on node: %s' % node_uuid)

            elif t == "usvc":
                self.logger.info('__application_onboarding()', 'Component is a Microservice')

            elif t == "application":
                self.logger.info('__application_onboarding()', 'Component is a Complex Application')
                self.__application_onboarding(mf.get("uuid"), mf.get("entity_description"))

            else:
                self.logger.error('__application_onboarding()', "Component type not recognized %s" % t)
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

    def __exit_gracefully(self, signal, frame):
        self.logger.info('__exit_gracefully()', 'Received signal: %d' % signal)
        self.logger.info('__exit_gracefully()', 'fosAgent exiting...')
        keys = list(self.__rtPlugins.keys())
        # TODO fix try catch
        for k in keys:
            try:
                self.__rtPlugins.get(k).stop_runtime()
            except Exception as e:
                self.logger.error('__exit_gracefully()', '{0}'.format(e))
                traceback.print_exc()
                pass
        keys = list(self.__nwPlugins.keys())
        for k in keys:
            try:
                self.__nwPlugins.get(k).stopNetwork()
            except Exception:
                self.logger.error('__exit_gracefully()', '{0}'.format(e))
                traceback.print_exc()
                pass

        self.dstore.close()
        self.astore.close()
        self.logger.info('__exit_gracefully()', '[ DONE ] Bye')
        #sys.exit(0)

    def run(self):


        uri = str('%s/onboard/*/' % self.dhome)
        self.dstore.observe(uri, self.__react_to_onboarding)
        self.logger.info('run()', 'fosAgent Observing for onboarding on: %s' % uri)

        uri = str('%s/*/' % self.dhome)
        self.dstore.observe(uri, self.__react_to_cache)
        self.logger.info('run()','fosAgent Observing home on: %s' % uri)

        uri = str('%s/plugins' % self.dhome)
        self.dstore.observe(uri, self.__react_to_plugins)
        self.logger.info('run()','fosAgent Observing plugins on: %s' % uri)

        #signal.signal(signal.SIGINT, self.__exit_gracefully)

        self.logger.info('run()','[ DONE ] fosAgent Up and Running')
        return self

    def stop(self):
        self.__exit_gracefully(2, None)





