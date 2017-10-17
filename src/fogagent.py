from interfaces.Agent import Agent
from PluginLoader import PluginLoader
import uuid
import sys
from DStore import *
#from RedisLocalCache import RedisCache
import json
import networkx as nx


class FogAgent(Agent):

    def __init__(self):
        self.PLUINGDIR ='./plugins'
        self.pl=PluginLoader(self.PLUINGDIR)
        self.pl.getPlugins()
        self.osPlugin = None
        self.rtPlugins = {}
        self.nwPlugins = {}
        self.loadOSPlugin()
        super(FogAgent, self).__init__(self.osPlugin.getUUID())
        sid = str(self.uuid)
        self.root = "fos://<sys-id>"
        self.home = str("fos://<sys-id>/%s" % sid)
        # Notice that a node may have multiple caches, but here we are
        # giving the same id to the nodew and the cache
        self.store = DStore(sid, self.root, self.home, 1024)

        val = {'status': 'add', 'version': self.osPlugin.version, 'description': 'linux plugin', 'plugin': ''}
        uri = str('fos://<sys-id>/%s/plugins/%s/%s' % (self.uuid, self.osPlugin.name, self.osPlugin.uuid))
        self.store.put(uri, json.dumps(val))

        val = {'plugins': [{'name': 'linux', 'version': self.osPlugin.version, 'uuid': str(self.osPlugin.uuid),
                           'type': 'os'}]}
        uri  = str('fos://<sys-id>/%s/plugins' % self.uuid)
        self.store.put(uri, json.dumps(val))

        self.populateNodeInformation()

    def loadOSPlugin(self):
        platform = sys.platform
        if platform == 'linux':
            print("I'am on Linux")
            os = self.pl.locatePlugin('linux')
            if os is not None:
                os = self.pl.loadPlugin(os)
                self.osPlugin = os.run()
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
        return self.osPlugin

    def loadRuntimePlugin(self, plugin_name):
        rt = self.pl.locatePlugin(plugin_name)
        if rt is not None:
            rt = self.pl.loadPlugin(rt)
            rt = rt.run(agent=self)
            self.rtPlugins.update({rt.uuid: rt})
            val = {'version': rt.version, 'description': str('runtime %s' % rt.name), 'plugin': ''}
            uri = str('fos://<sys-id>/%s/plugins/%s/%s' % (self.uuid, rt.name, rt.uuid))
            self.store.put(uri, json.dumps(val))

            val = {'plugins': [{'name': rt.name, 'version': rt.version, 'uuid': str(rt.uuid),
                                'type': 'runtime', 'status': 'loaded'}]}
            uri = str('fos://<sys-id>/%s/plugins' % self.uuid)
            self.store.dput(uri, json.dumps(val))

            return rt
        else:
            return None

    def loadNetworkPlugin(self, plugin_name):
        net = self.pl.locatePlugin(plugin_name)
        if net is not None:
            net = self.pl.loadPlugin(net)
            net = net.run(agent=self)
            self.rtPlugins.update({net.uuid: net})

            val = {'version': net.version, 'description': str('runtime %s' % net.name),
                   'plugin': ''}
            uri = str('fos://<sys-id>/%s/plugins/%s/%s' % (self.uuid, net.name, net.uuid))
            self.store.put(uri, json.dumps(val))

            val = {'plugins': [{'name': net.name, 'version': net.version, 'uuid': str(net.uuid),
                                'type': 'network','status': 'loaded'}]}
            uri = str('fos://<sys-id>/%s/plugins' % self.uuid)
            self.store.dput(uri, json.dumps(val))

            return net
        else:
            return None

    def populateNodeInformation(self):

        node_info = {}
        node_info.update({'uuid': str(self.uuid)})
        node_info.update({'name': self.osPlugin.get_hostname()})
        node_info.update({'cpu': self.osPlugin.getProcessorInformation()})
        node_info.update({'ram': self.osPlugin.getMemoryInformation()})
        node_info.update({'disks': self.osPlugin.getDisksInformation()})
        node_info.update({'network': self.osPlugin.getNetworkInformations()})

        uri = str('fos://<sys-id>/%s/' % self.uuid)
        self.store.put(uri, json.dumps(node_info))

    def reactToCache(self, uri, value, v):
        print ("###########################")
        print ("##### I'M an Observer #####")
        print ("## Key: %s" % uri)
        print ("## Value: %s" % value)
        print ("## V: %s" % v)
        print ("###########################")
        print ("###########################")

    def reactToPlugins(self, uri, value, v):
        print("Received a plugins action")
        print (value)
        value = json.loads(value)
        value = value.get('plugins')
        for v in value:
            if v.get('status') == 'add':
                print (v)
                print("I should add a plugin")
                name = v.get('name')

                #@TODO: use a dict with functions instead of if elif else...
                if v.get('type') == 'runtime':
                    rt = self.loadRuntimePlugin(name)
                    self.rtPlugins.update({rt.uuid: rt})
                elif v.get('type') == 'network':
                    nw = self.loadNetworkPlugin(name)
                    self.nwPlugins.update({nw.uuid: nw})
                else:
                    print('Plugins of type %s are not yet supported...' % v.get('type'))

    def applicationDefinition(self, uri, value, v):
        '''
        This should observe fos://<sys-id>/nodeid/applications/*
        Where each application is defined like the example in the docs
        So to add an application someone should always do a dput

        Example service:
         {
        "name":"wp_blog"
        "description":"simple wordpress blog",
        "components":[
                {
                    "name":"wordpress",
                    "need":["mysql"],
                    "proximity":{"mysql":3}
                    "manifest":"fos://sys-id/node-id/applications/appuuid/component_name"
                },
                {
                    "name":"mysql",
                    "need":[],
                    "proximity":{},
                    "manifest":"fos://sys-id/node-id/applications/appuuid/component_name"
                }
            ]
        }

        service components:
        {
            "name":"wp_v2.foo.bar"
            "description":"wordpress blog engine",
            "version": 2,
            "type":"container",
            "entity_description":{...},
            "accelerators":[]
            "io":[]
        }



        {
            "name":"myql_v2.foo.bar"
            "description":"mysql db engine",
            "version" : 3,
            "type":"vm",
            "entity_description":{...},  <- here all information to download and configure the db server
            "accelerators":[]
            "io":[]
        }

        Then starting from these the agent should create the right entities json and write in the correct uris in the
        correct order and in the correct nodes

        So in this case should create:

        for mysql:
        {'status': 'define', 'name': 'mysql_v2.foo.bar, 'version': 1, 'entity_data': entity_description}

        then write this to
        fos://sysid/nodeid/runtime/kvmid/this_entity_id
        and configure and start this vm

        for mysql
        {'status': 'define', 'name': 'wp_v2.foo.bar, 'version': 1, 'entity_data': entity_description}
        where entity_description should be populated from information based on previous mysql deployment
        (eg. server ip)
        then write this to (nodeid can be the same or another, choice is based on proximity definition in app manifest
        fos://sysid/nodeid/runtime/lxc_id/wp_entity_id
        and configure and start this container

        after these steps the service should work and his information should be available in his uri

        :param uri:
        :param value:
        :param v:
        :return:
        '''

        print("URI: %s\nValue: %s\nVersion: %s\n" % (uri, value, v))

        value = json.loads(value)

        application_uuid = uri.split('/')[-1]
        print (application_uuid)
        deploy_order_list = self.resolve_dependencies(value.get('components', None))
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
            mf = self.get_manifest(component.get('manifest'))
            '''
            from this manifest generate the correct json 
            '''
            t = mf.get('type')

            if t == "kvm":
                print("component is a vm")
                kvm = self.search_plugin_by_name('KVM')
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

                uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s' % (node_uuid, kvm.get('uuid'), vm_uuid))
                self.store.put(uri, json_data)

                time.sleep(1)

                uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s#status=configure' %
                          (node_uuid, kvm.get('uuid'), vm_uuid))
                self.store.dput(uri)

                # HERE SHOULD WAIT FOR VM TO BE READY TO START
                input("press to start")

                uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s#status=run' %
                          (node_uuid, kvm.get('uuid'), vm_uuid))
                self.store.dput(uri)


                input("press to continue")
                #input("press to stop")
                #uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s#status=stop' % (node_uuid, kvm.get('uuid'), vm_uuid))
                #self.store.dput(uri)

                #time.sleep(1)

                #uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s#status=clean' %
                #          (node_uuid, kvm.get('uuid'), vm_uuid))
                #self.store.dput(uri)

                #time.sleep(1)
                #uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s#status=undefine' %
                #          (node_uuid, kvm.get('uuid'), vm_uuid))
                #self.store.dput(uri)

                # HERE SHOULD WAIT FOR VM TO BE STARTED BEFORE DEPLOY NEXT ONES

                #uri = str('fos://<sys-id>/%s/runime/%s/entity/%s/info' % (node_uuid, kvm.get('uuid'), vm_uuid))
                #informations.update({c: json.loads(self.store.get(uri))})



            elif t == "container":
                print("component is a container")
            elif t == "native":
                print("component is a native application")
                native = self.search_plugin_by_name('native')
                if native is None:
                    print ('native is NONE!!')
                    return False

                node_uuid = str(self.uuid)  # @TODO: select deploy node in a smart way
                na_uuid = mf.get("entity_description").get("uuid")

                entity_definition = {'status': 'define', 'name': component.get("name"), 'version': component.get(
                    'version'), 'entity_data': mf.get("entity_description")}
                json_data = json.dumps(entity_definition)

                uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s' % (node_uuid, native.get('uuid'), na_uuid))
                self.store.put(uri, json_data)

                time.sleep(1)

                uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s#status=configure' %
                          (node_uuid, native.get('uuid'), na_uuid))
                self.store.dput(uri)

                # HERE SHOULD WAIT FOR VM TO BE READY TO START
                input("press to start")

                uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s#status=run' %
                          (node_uuid, native.get('uuid'), na_uuid))
                self.store.dput(uri)

                input("press to stop")
                uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s#status=stop' % (node_uuid, kvm.get('uuid'), na_uuid))
                self.store.dput(uri)

                time.sleep(1)

                uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s#status=clean' %
                          (node_uuid, native.get('uuid'), na_uuid))
                self.store.dput(uri)

                time.sleep(1)
                uri = str('fos://<sys-id>/%s/runtime/%s/entity/%s#status=undefine' %
                          (node_uuid, native.get('uuid'), na_uuid))
                self.store.dput(uri)




            elif t == "ros":
                print("component is a ros application")
            elif t == "usvc":
                print("component is a microservice")
            else:
                raise AssertionError("Component type not recognized %s" % t)
                return

    def resolve_dependencies(self, components):
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

    def get_manifest(self, manifest_path):
        return json.loads(self.store.get(manifest_path))

    def search_plugin_by_name(self, name):
        uri = str('fos://<sys-id>/%s/plugins' % self.uuid)
        all_plugins = json.loads(self.store.get(uri)).get('plugins')
        search = [x for x in all_plugins if name in x.get('name')]
        if len(search) == 0:
            return None
        else:
            return search[0]

    def main(self):



        #print(self.store)

        #self.loadRuntimePlugin('KVMLibvirt')
        #self.loadNetworkPlugin('brctl')

        #print (self.store)
        uri = str('fos://<sys-id>/%s/applications/*/' % self.uuid)
        self.store.observe(uri, self.applicationDefinition)


        uri = str('fos://<sys-id>/%s/*/' % self.uuid)
        self.store.observe(uri, self.reactToCache)

        uri = str('fos://<sys-id>/%s/plugins' % self.uuid)
        self.store.observe(uri, self.reactToPlugins)




        print("Listening on Store...")
        while True:
            time.sleep(100)



if __name__=='__main__':
    print(" _____            ___  ____\n|  ___|__   __ _ / _ \/ ___|\n| |_ / _ \ / _` | | | \___ \ \n|  _| (_) | (_| "
          "| |_| |___) |\n|_|  \___/ \__, |\___/|____/\n           |___/")
    agent = FogAgent()
    agent.main()

