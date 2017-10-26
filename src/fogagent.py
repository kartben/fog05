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


class FogAgent(Agent):

    def __init__(self):
        self.__PLUINGDIR = './plugins'
        self.pl=PluginLoader(self.__PLUINGDIR)
        self.pl.getPlugins()
        self.__osPlugin = None
        self.__rtPlugins = {}
        self.__nwPlugins = {}
        self.__load_os_plugin()
        super(FogAgent, self).__init__(self.__osPlugin.getUUID())
        sid = str(self.uuid)

        # Desidered Store. containing the desidered state
        self.droot = "dfos://<sys-id>"
        self.dhome = str("dfos://<sys-id>/%s" % sid)
        self.dstore = DStore(sid, self.droot, self.dhome, 1024)

        # Actual Store, containing the Actual State
        self.aroot = "afos://<sys-id>"
        self.ahome = str("afos://<sys-id>/%s" % sid)
        self.astore = DStore(sid, self.aroot, self.ahome, 1024)

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

    def __load_os_plugin(self):
        platform = sys.platform
        if platform == 'linux':
            print("I'am on Linux")
            os = self.pl.locatePlugin('linux')
            if os is not None:
                os = self.pl.loadPlugin(os)
                self.__osPlugin = os.run()
            else:
                raise RuntimeError("Error on loading OS Plugin")
        elif platform == 'darwin':
            print("I'am on Mac")
            raise RuntimeError("Mac plugin not yet implemented...")
        elif platform == 'windows':
            print("I'am on Windows")
            raise RuntimeError("Windows plugin not yet implemented...")
        else:
            raise RuntimeError("Platform not compatible")



    def getOSPlugin(self):
        return self.__osPlugin

    def __load_runtime_plugin(self, plugin_name):
        rt = self.pl.locatePlugin(plugin_name)
        if rt is not None:
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

            return rt
        else:
            return None

    def __load_network_plugin(self, plugin_name):
        net = self.pl.locatePlugin(plugin_name)
        if net is not None:
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

            return net
        else:
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
        print("Received a plugins action")
        print(value)
        value = json.loads(value)
        value = value.get('plugins')
        for v in value:
            if v.get('status') == 'add':
                print (v)
                print("I should add a plugin")
                name = v.get('name')

                #@TODO: use a dict with functions instead of if elif else...
                if v.get('type') == 'runtime':
                    rt = self.__load_runtime_plugin(name)
                    self.__rtPlugins.update({rt.uuid: rt})
                elif v.get('type') == 'network':
                    nw = self.__load_network_plugin(name)
                    self.__nwPlugins.update({nw.uuid: nw})
                else:
                    print('Plugins of type %s are not yet supported...' % v.get('type'))


    def __react_to_onboarding(self, uri, value, v):
        print("URI: %s\nValue: %s\nVersion: %s\n" % (uri, value, v))
        value = json.loads(value)
        application_uuid = uri.split('/')[-1]
        self.__application_onboarding(application_uuid,value)


    def __application_onboarding(self,application_uuid, value):




        print(application_uuid)
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
                raise AssertionError("Could not find component in component list WTF?")
                return

            '''
            Should recover in some way the component manifest
            
            '''
            mf = self.__get_manifest(component.get('manifest'))
            '''
            from this manifest generate the correct json 
            '''
            t = mf.get('type')

            if t == "kvm":
                print("component is a vm")
                kvm = self.__search_plugin_by_name('KVM')
                if kvm is None:
                    print ('KVM is NONE!!')
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

                uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s' % (node_uuid, kvm.get('uuid'), vm_uuid))
                self.dstore.put(uri, json_data)

                while True:
                    print("Waiting vm defined...")
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, kvm.get('uuid'), vm_uuid))
                    vm_info = json.loads(self.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "defined":
                        break

                uri = str(
                    'dfos://<sys-id>/%s/runtime/%s/entity/%s#status=configure' % (node_uuid, kvm.get('uuid'), vm_uuid))
                self.dstore.dput(uri)

                while True:
                    print("Waiting vm configured...")
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, kvm.get('uuid'), vm_uuid))
                    vm_info = json.loads(self.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "configured":
                        break

                uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s#status=run' % (node_uuid, kvm.get('uuid'), vm_uuid))
                self.dstore.dput(uri)

                while True:
                    print("Waiting vm to boot...")
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, kvm.get('uuid'), vm_uuid))
                    vm_info = json.loads(self.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "run":
                        break

                print("vm is running on node")




            elif t == "container":
                print("component is a container")
            elif t == "native":
                print("component is a native application")
                native = self.__search_plugin_by_name('native')
                if native is None:
                    print ('native is NONE!!')
                    return False

                node_uuid = str(self.uuid)  # @TODO: select deploy node in a smart way
                na_uuid = mf.get("entity_description").get("uuid")

                entity_definition = {'status': 'define', 'name': component.get("name"), 'version': component.get(
                    'version'), 'entity_data': mf.get("entity_description")}
                json_data = json.dumps(entity_definition)

                uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s' % (node_uuid, native.get('uuid'), na_uuid))
                self.sdtore.put(uri, json_data)

                while True:
                    print("Waiting native to defined...")
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, native.get('uuid'), na_uuid))
                    vm_info = json.loads(self.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "defined":
                        break

                uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s#status=configure' %
                          (node_uuid, native.get('uuid'), na_uuid))
                self.dstore.dput(uri)

                while True:
                    print("Waiting native to configure...")
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, native.get('uuid'), na_uuid))
                    vm_info = json.loads(self.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "configured":
                        break

                uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s#status=run' %
                          (node_uuid, native.get('uuid'), na_uuid))
                self.store.dput(uri)

                while True:
                    print("Waiting native to start...")
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, native.get('uuid'), na_uuid))
                    vm_info = json.loads(self.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "run":
                        break


                print ("native started")



            elif t == "ros":
                print("component is a ros application")
            elif t == "usvc":
                print("component is a microservice")

            elif t == "application":
                self.__application_onboarding(mf.get("uuid"),mf.get("entity_description"))

            else:
                raise AssertionError("Component type not recognized %s" % t)
                return

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
            print (no_dependable_components)
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
        return json.loads(self.store.get(manifest_path))

    def __search_plugin_by_name(self, name):
        uri = str('%s/plugins' % self.ahome)
        all_plugins = json.loads(self.store.get(uri)).get('plugins')
        search = [x for x in all_plugins if name in x.get('name')]
        if len(search) == 0:
            return None
        else:
            return search[0]

    def __wait_boot(self, filename):
        time.sleep(5)
        boot_regex = r"\[.+?\].+\[.+?\]:.+Cloud-init.+?v..+running.+'modules:final'.+Up.([0-9]*\.?[0-9]+).+seconds.\n"
        while True:
            file = open(filename, 'r')
            import os
            # Find the size of the file and move to the end
            st_results = os.stat(filename)
            st_size = st_results[6]
            file.seek(st_size)

            while 1:
                where = file.tell()
                line = file.readline()
                if not line:
                    time.sleep(1)
                    file.seek(where)
                else:
                    m = re.search(boot_regex, str(line))
                    if m:
                        found = m.group(1)
                        return found



    def main(self):



        #print(self.store)

        #self.loadRuntimePlugin('KVMLibvirt')
        #self.loadNetworkPlugin('brctl')

        #print (self.store)
        uri = str('%s/onboard/*/' % self.dhome)
        print("Applications URI: %s" % uri)
        self.dstore.observe(uri, self.__application_onboarding)

        uri = str('%s/*/' % self.dhome)
        print("Home URI: %s" % uri)
        self.dstore.observe(uri, self.__react_to_cache)

        uri = str('%s/plugins' % self.dhome)
        print("Plugins URI: %s" %uri)
        self.dstore.observe(uri, self.__react_to_plugins)

        print("Listening on Store...")
        while True:
            time.sleep(100)







if __name__=='__main__':
    print(" _____            ___  ____\n|  ___|__   __ _ / _ \/ ___|\n| |_ / _ \ / _` | | | \___ \ \n|  _| (_) | (_| "
          "| |_| |___) |\n|_|  \___/ \__, |\___/|____/\n           |___/")
    agent = FogAgent()
    agent.main()

