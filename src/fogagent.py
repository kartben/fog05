from interfaces.Agent import Agent
from PluginLoader import PluginLoader
import uuid
import sys
from DStore import *
#from RedisLocalCache import RedisCache
import json


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
                    "manifest":"/some/path/to/wordpress_manifest.json"
                },
                {
                    "name":"mysql",
                    "need":[],
                    "proximity":{"wp_blog":3},
                    "manifest":"/some/path/to/mysql_manifest.json"
                }
            ]
        }

        service components:
        {
            "name":"wp_v2.foo.bar"
            "description":"wordpress blog engine"
            "type":"container",
            "entity_description":{...},
            "accelerators":[]
            "io":[]
        }



        {
            "name":"myql_v2.foo.bar"
            "description":"mysql db engine"
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

        deploy_order_list = self.resolve_dependencies(value.get('components', None))



    def resolve_dependencies(self,components):
        '''
        The return list should be only a list of name of components in the order the should be deployed
        :param components: list like [{'name': 'c1', 'need': ['c2', 'c3']}, {'name': 'c2', 'need': ['c3']}, {'name': 'c3', 'need': ['c4']}, {'name': 'c4', 'need': []}, {'name': 'c5', 'need': []}]
        :return: list like [[{'name': 'c4', 'need': []}, {'name': 'c5', 'need': []}], [{'name': 'c3', 'need': []}], [{'name': 'c2', 'need': []}], [{'name': 'c1', 'need': []}], []]
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

        return no_dependable_components

    def main(self):



        #print(self.store)

        #self.loadRuntimePlugin('KVMLibvirt')
        #self.loadNetworkPlugin('brctl')

        #print (self.store)

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

