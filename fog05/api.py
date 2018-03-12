from jsonschema import validate, ValidationError
from fog05 import Schemas
from dstore import Store
from enum import Enum
import re
import uuid

class FOSStore(object):

    def __init__(self, aroot, droot, home):
        self.aroot = aroot  # 'dfos://{}'
        self.ahome = str('{}/{}'.format(aroot, home))  # str('dfos://{}/{}' % self.uuid)

        self.droot = droot  # 'dfos://{}'
        self.dhome = str('{}/{}'.format(droot, home))  # str('dfos://{}/{}' % self.uuid)

        self.actual = Store('a{}'.format(home), self.aroot, self.ahome, 1024)
        self.desired = Store('d{}'.format(home), self.droot, self.dhome, 1024)

    def close(self):
        pass
        self.actual.close()
        self.desired.close()

    '''
    This class allow the interaction with fog05 using simple Python3 API
    Need the distributed store
    
    '''


class API(object):

    def __init__(self, sysid=0):

        self.a_root = 'afos://{}'.format(sysid)
        self.d_root = 'dfos://{}'.format(sysid)
        self.store = FOSStore(self.a_root, self.d_root, 'python-api')

        self.manifest = self.Manifest(self.store)
        self.node = self.Node(self.store)
        self.plugin = self.Plugin(self.store)
        self.network = self.Network(self.store)
        self.entity = self.Entity(self.store)
        self.image = self.Image(self.store)
        self.flavor = self.Flavor(self.store)

    class Manifest(object):
        def __init__(self, store=None):
            if store is None:
                raise RuntimeError('store cannot be none in API!')
            self.store = store

        def check(self, manifest, manifest_type):
            if manifest_type == self.Type.ENTITY:
                t = manifest.get('type')
                try:
                    if t == 'vm':
                        validate(manifest.get('entity_data'), Schemas.vm_schema)
                    elif t == 'container':
                        validate(manifest.get('entity_data'), Schemas.container_schema)
                    elif t == 'native':
                        validate(manifest.get('entity_data'), Schemas.native_schema)
                    elif t == 'ros2':
                        validate(manifest.get('entity_data'), Schemas.ros2_schema)
                    elif t == 'usvc':
                        return False
                    else:
                        return False
                except ValidationError as ve:
                    return False
            if manifest_type == self.Type.NETWORK:
                try:
                    validate(manifest, Schemas.network_schema)
                except ValidationError as ve:
                    return False
            if manifest_type == self.Type.ENTITY:
                try:
                    validate(manifest, Schemas.entity_schema)
                except ValidationError as ve:
                    return False

            return True

        class Type(Enum):
            '''
            States of entities
            '''
            ENTITY = 0
            IMAGE = 1
            FLAVOR = 3
            NETWORK = 4
            PLUGIN = 5

    class Node(object):
        def __init__(self, store=None):
            if store is None:
                raise RuntimeError('store cannot be none in API!')
            self.store = store

        def list(self):
            '''

            :return: list of tuples (uuid, hostname)
            '''
            nodes = []
            uri = '{}/*'.format(self.store.aroot)
            infos = self.store.actual.resolveAll(uri)
            for i in infos:
                if len(i[0].split('/')) == 4:
                    node_info = json.loads(i[1])
                    nodes.append((node_info.get('uuid'), node_info.get('name')))
            return nodes

        def info(self, node_uuid):
            """
            Provide all information about a specific node

            :param node_uuid: the uuid of the node you want info
            :return: a dictionary with all infomarion about the node
            """
            if node_uuid is None:
                return None
            uri = '{}/{}'.format(self.store.aroot, node_uuid)
            infos = self.store.actual.resolve(uri)
            if infos is None:
                return None
            return json.loads(infos)

        def plugins(self, node_uuid):
            uri = '{}/{}/plugins'.format(self.store.aroot, node_uuid)
            response = self.store.actual.get(uri)
            if response is not None:
                return json.loads(response).get('plugins')
            else:
                return None

        def search(self, search_dict):
            pass

    class Plugin(object):
        def __init__(self, store=None):
            if store is None:
                raise RuntimeError('store cannot be none in API!')
            self.store = store

        def add(self, manifest, node_uuid=None):
            manifest.update({'status':'add'})
            plugins = {"plugins": [manifest]}
            plugins = json.dumps(plugins).replace(' ', '')
            if node_uuid is None:
                uri = '{}/*/plugins'.format(self.store.droot)
            else:
                uri = '{}/{}/plugins'.format(self.store.droot, node_uuid)

            res = self.store.desired.dput(uri, plugins)
            if res:
                return True
            else:
                return False

        def remove(self, plugin_uuid, node_uuid=None):
            pass

        def list(self, node_uuid=None):
            '''


            :param node_uuid: can be none
            :return: dictionary {node_uuid, plugin list }
            '''
            if node_uuid is not None:

                uri = '{}/{}/plugins'.format(self.store.aroot, node_uuid)
                response = self.store.actual.get(uri)
                if response is not None:
                    return {node_uuid:json.loads(response).get('plugins')}
                else:
                    return None

            plugins = {}
            uri = '{}/*/plugins'.format(self.store.aroot)
            response = self.store.actual.resolveAll(uri)
            for i in response:
                id = i[0].split('/')[2]
                pl = json.loads(i[1]).get('plugins')
                plugins.update({id: pl})
            return plugins

        def search(self, search_dict, node_uuid=None):
            pass

    class Network(object):
        def __init__(self, store=None):
            if store is None:
                raise RuntimeError('store cannot be none in API!')
            self.store = store

        def add(self, manifest, node_uuid=None):
            manifest.update({'status': 'add'})
            json_data = json.dumps(manifest).replace(' ', '')

            if node_uuid is not None:
                uri = '{}/{}/network/*/networks/{}'.format(self.store.droot, node_uuid, manifest.get('uuid'))
            else:
                uri = '{}/*/network/*/networks/{}'.format(self.store.droot, manifest.get('uuid'))

            res = self.store.desired.put(uri, json_data)
            if res:
                return True
            else:
                return False

        def remove(self, net_uuid, node_uuid=None):
            if node_uuid is not None:
                uri = '{}/{}/network/*/networks/{}'.format(self.store.droot, node_uuid, net_uuid)
            else:
                uri = '{}/*/network/*/networks/{}'.format(self.store.droot, net_uuid)

            res = self.store.desired.remove(uri)
            if res:
                return True
            else:
                return False

        def list(self, node_uuid=None):
            if node_uuid is not None:
                n_list = []
                uri = '{}/{}/network/*/networks/'.format(self.store.aroot, node_uuid)
                response = self.store.actual.resolveAll(uri)
                for i in response:
                    n_list.append(json.loads(i[1]))
                return {node_uuid: n_list}

            nets = {}
            uri = '{}/*/network/*/networks/'.format(self.store.aroot)
            response = self.store.actual.resolveAll(uri)
            for i in response:
                id = i[0].split('/')[2]
                net = json.loads(i[1])
                net_list = nets.get(id, None)
                if net_list is None:
                    net_list = []
                net_list.append(net)
                nets.update({id: net_list})
            return nets

        def search(self, search_dict, node_uuid=None):
            pass

    class Entity(object):
        def __init__(self, store=None):
            if store is None:
                raise RuntimeError('store cannot be none in API!')
            self.store = store

        def __search_plugin_by_name(self, name, node_uuid):
            uri = '{}/{}/plugins'.format(self.store.aroot, node_uuid)
            all_plugins = self.store.actual.get(uri)
            if all_plugins is None or all_plugins == '':
                print('Cannot get plugin')
                return None
            all_plugins = json.loads(all_plugins).get('plugins')
            search = [x for x in all_plugins if name.upper() in x.get('name').upper()]
            if len(search) == 0:
                return None
            else:
                return search[0]

        def __get_entity_handler_by_uuid(self, node_uuid, entity_uuid):
            uri = '{}/{}/runtime/*/entity/{}'.format(self.store.aroot, node_uuid, entity_uuid)
            all = self.store.actual.resolveAll(uri)
            for i in all:
                k = i[0]
                if fnmatch.fnmatch(k, uri):
                    # print('MATCH {0}'.format(k))
                    # print('Extracting uuid...')
                    regex = uri.replace('/', '\/')
                    regex = regex.replace('*', '(.*)')
                    reobj = re.compile(regex)
                    mobj = reobj.match(k)
                    uuid = mobj.group(1)
                    # print('UUID {0}'.format(uuid))

                    return uuid

        def __get_entity_handler_by_type(self, node_uuid, t):
            handler = None
            handler = self.__search_plugin_by_name(t, node_uuid)
            if handler is None:
                print('type not yet supported')
            return handler

        def add(self, manifest, node_uuid, wait=False):
            '''
            define, configure and run an entity all in one shot
            :param manifest:
            :param node_uuid:
            :param wait:
            :return: the instance uuid
            '''
            pass

        def remove(self, entity_uuid, node_uuid, wait=False):
            '''

            stop, clean and undefine entity all in one shot

            :param entity_uuid:
            :param node_uuid:
            :param wait:
            :return: the instance uuid
            '''
            pass

        def define(self, manifest, node_uuid, wait=False):
            manifest.update({'status': 'define'})
            handler = None
            t = manifest.get('type')
            try:
                if t in ['kvm', 'xen']:
                    handler = self.__search_plugin_by_name(t, node_uuid)
                    validate(manifest.get('entity_data'), Schemas.vm_schema)
                elif t in ['container', 'lxd']:
                    handler = self.__search_plugin_by_name(t, node_uuid)
                    validate(manifest.get('entity_data'), Schemas.container_schema)
                elif t == 'native':
                    handler = self.__search_plugin_by_name('native', node_uuid)
                    validate(manifest.get('entity_data'), Schemas.native_schema)
                elif t == 'ros2':
                    handler = self.__search_plugin_by_name('ros2', node_uuid)
                    validate(manifest.get('entity_data'), Schemas.ros2_schema)
                elif t == 'usvc':
                    print('microservice not yet')
                else:
                    print('type not recognized')

                if handler is None:
                    return False
            except ValidationError as ve:
                return False

            entity_uuid = manifest.get('uuid')
            entity_definition = manifest
            json_data = json.dumps(entity_definition).replace(' ', '')
            uri = '{}/{}/runtime/{}/entity/{}'.format(self.store.droot, node_uuid, handler.get('uuid'), entity_uuid)

            res = self.store.desired.put(uri, json_data)
            if res:

                if wait:
                    while True:
                        time.sleep(1)
                        uri = '{}/{}/runtime/{}/entity/{}'.format(self.store.aroot, node_uuid, handler.get('uuid'), entity_uuid)
                        data = self.store.actual.get(uri)
                        entity_info = None
                        if data is not None:
                            entity_info = json.loads(data)
                            if entity_info is not None and entity_info.get('status') == 'defined':
                                break
                return True
            else:
                return False

        def undefine(self, entity_uuid, node_uuid, wait=False):
            handler = self.__get_entity_handler_by_uuid(node_uuid, entity_uuid)
            uri = '{}/{}/runtime/{}/entity/{}'.format(self.store.droot, node_uuid, handler, entity_uuid)

            res = self.store.desired.remove(uri)
            if res:
                return True
            else:
                return False

        def configure(self, entity_uuid, node_uuid, instance_uuid=None, wait=False):
            handler = self.__get_entity_handler_by_uuid(node_uuid, entity_uuid)
            if instance_uuid is None:
                instance_uuid = '{}'.format(uuid.uuid4())

            uri = '{}/{}/runtime/{}/entity/{}/instance/{}#status=configure'.format(self.store.droot, node_uuid, handler, entity_uuid, instance_uuid)
            res = self.store.desired.dput(uri)
            if res:
                if wait:
                    while True:
                        time.sleep(1)
                        uri = '{}/{}/runtime/{}/entity/{}/instance/{}'.format(self.store.aroot, node_uuid, handler, entity_uuid, instance_uuid)
                        data = self.store.actual.get(uri)
                        entity_info = None
                        if data is not None:
                            entity_info = json.loads(data)
                            if entity_info is not None and entity_info.get('status') == 'configured':
                                break
                return instance_uuid
            else:
                return None

        def clean(self, entity_uuid, node_uuid, instance_uuid, wait=False):
            handler = yield from self.__get_entity_handler_by_uuid(node_uuid, entity_uuid)
            uri = '{}/{}/runtime/{}/entity/{}/instance/{}'.format(self.store.aroot, node_uuid, handler, entity_uuid, instance_uuid)
            res = self.store.desired.remove(uri)
            if res:
                return True
            else:
                return False

        def run(self, entity_uuid, node_uuid, instance_uuid, wait=False):
            handler = self.__get_entity_handler_by_uuid(node_uuid, entity_uuid)
            uri = '{}/{}/runtime/{}/entity/{}/instance/{}#status=run'.format(self.store.droot, node_uuid, handler, entity_uuid, instance_uuid)
            res = self.store.desired.dput(uri)
            if res:
                if wait:
                    while True:
                        time.sleep(1)
                        uri = '{}/{}/runtime/{}/entity/{}/instance/{}'.format(self.store.aroot, node_uuid, handler, entity_uuid, instance_uuid)
                        data = yield from self.store.actual.get(uri)
                        entity_info = None
                        if data is not None:
                            entity_info = json.loads(data)
                            if entity_info is not None and entity_info.get('status') == 'run':
                                break
                return True
            else:
                return False

        def stop(self, entity_uuid, node_uuid, instance_uuid, wait=False):
            handler = self.__get_entity_handler_by_uuid(node_uuid, entity_uuid)
            uri = '{}/{}/runtime/{}/entity/{}/instance/{}#status=stop'.format(self.store.droot, node_uuid, handler, entity_uuid, instance_uuid)
            res = self.store.desired.dput(uri)
            if res:
                if wait:
                    while True:
                        uri = '{}/{}/runtime/{}/entity/{}/instance/{}'.format(self.store.aroot, node_uuid, handler, entity_uuid, instance_uuid)
                        data = self.store.actual.get(uri)
                        entity_info = None
                        if data is not None:
                            entity_info = json.loads(data)
                            if entity_info is not None and entity_info.get('status') == 'stop':
                                break
                return True
            else:
                return False

        def pause(self, entity_uuid, node_uuid, instance_uuid, wait=False):
            handler = self.__get_entity_handler_by_uuid(node_uuid, entity_uuid)
            uri = '{}/{}/runtime/{}/entity/{}/instance/{}#status=pause'.format(self.store.droot, node_uuid, handler, entity_uuid, instance_uuid)
            res = self.store.desired.dput(uri)
            if res:
                if wait:
                    while True:
                        uri = '{}/{}/runtime/{}/entity/{}/instance/{}'.format(self.store.aroot, node_uuid, handler, entity_uuid, instance_uuid)
                        data = self.store.actual.get(uri)
                        entity_info = None
                        if data is not None:
                            entity_info = json.loads(data)
                            if entity_info is not None and entity_info.get('status') == 'pause':
                                break
                return True
            else:
                return False

        def resume(self, entity_uuid, node_uuid, instance_uuid, wait=False):
            handler = self.__get_entity_handler_by_uuid(node_uuid, entity_uuid)
            uri = '{}/{}/runtime/{}/entity/{}/instance/{}#status=resume'.format(self.store.droot, node_uuid, handler, entity_uuid, instance_uuid)
            res = self.store.desired.dput(uri)
            if res:
                if wait:
                    while True:
                        uri = '{}/{}/runtime/{}/entity/{}/instance/{}'.format(self.store.aroot, node_uuid, handler, entity_uuid, instance_uuid)
                        data = self.store.actual.get(uri)
                        entity_info = None
                        if data is not None:
                            entity_info = json.loads(data)
                            if entity_info is not None and entity_info.get('status') == 'run':
                                break
                return True
            else:
                return False

        def migrate(self, entity_uuid, instance_uuid, node_uuid, destination_node_uuid, wait=False):
            handler = self.__get_entity_handler_by_uuid(node_uuid, entity_uuid)
            uri = '{}/{}/runtime/{}/entity/{}/instance/{}'.format(self.store.aroot, node_uuid, handler, entity_uuid, instance_uuid)

            entity_info = self.store.actual.get(uri)
            if entity_info is None:
                return False

            entity_info = json.loads(entity_info)

            entity_info_src = entity_info.copy()
            entity_info_dst = entity_info.copy()

            entity_info_src.update({"status": "taking_off"})
            entity_info_src.update({"dst": destination_node_uuid})

            entity_info_dst.update({"status": "landing"})
            entity_info_dst.update({"dst": destination_node_uuid})

            destination_handler = self.__get_entity_handler_by_type(destination_node_uuid, entity_info_dst.get('type'))
            if destination_handler is None:
                return False

            uri = '{}/{}/runtime/{}/entity/{}/instance/{}'.format(self.store.droot, destination_node_uuid, destination_handler.get('uuid'), entity_uuid, instance_uuid)

            res = self.store.desired.put(uri, json.dumps(entity_info_dst).replace(' ', ''))
            if res:
                uri = '{}/{}/runtime/{}/entity/{}/instance/{}'.format(self.droot, node_uuid, handler, entity_uuid, instance_uuid)
                res_dest = yield from self.store.desired.dput(uri, json.dumps(entity_info_src).replace(' ', ''))
                if res_dest:
                    if wait:
                        while True:
                            time.sleep(1)
                            uri = "{}/{}/runtime/{}/entity/{}/instance/{}".format(self.aroot, destination_node_uuid, destination_handler.get('uuid'), entity_uuid, instance_uuid)
                            data = yield from self.store.actual.get(uri)
                            entity_info = None
                            if data is not None:
                                entity_info = json.loads(data)
                            if entity_info is not None and entity_info.get("status") == "run":
                                break
                    return True
                else:
                    print("Error on destination node")
                    return False
            else:
                print("Error on source node")
                return False

        def search(self, search_dict, node_uuid=None):
            pass

    class Image(object):
        def __init__(self, store=None):
            if store is None:
                raise RuntimeError('store cannot be none in API!')
            self.store = store

        def add(self, manifest, node_uuid=None):
            manifest.update({'status': 'add'})
            json_data = json.dumps(manifest).replace(' ', '')
            if node_uuid is None:
                uri = '{}/*/runtime/*/image/{}'.format(self.store.droot, manifest.get('uuid'))
            else:
                uri = '{}/{}/runtime/*/image/{}'.format(self.store.droot, node_uuid, manifest.get('uuid'))
            res = self.store.desired.put(uri, json_data)
            if res:
                return True
            else:
                return False

        def remove(self, image_uuid, node_uuid=None):
            if node_uuid is None:
                uri = '{}/*/runtime/*/image/{}'.format(self.store.droot, image_uuid)
            else:
                uri = '{}/{}/runtime/*/image/{}'.format(self.store.droot, node_uuid, image_uuid)
            res = self.store.desired.remove(uri)
            if res:
                return True
            else:
                return False

        def search(self, search_dict, node_uuid=None):
            pass

    class Flavor(object):
        def __init__(self, store=None):
            if store is None:
                raise RuntimeError('store cannot be none in API!')
            self.store = store

        def add(self, manifest, node_uuid=None):
            manifest.update({'status': 'add'})
            json_data = json.dumps(manifest).replace(' ', '')
            if node_uuid is None:
                uri = '{}/*/runtime/*/flavor/{}'.format(self.store.droot, manifest.get('uuid'))
            else:
                uri = '{}/{}/runtime/*/flavor/{}'.format(self.store.droot, node_uuid, manifest.get('uuid'))
            res = self.store.desired.put(uri, json_data)
            if res:
                return True
            else:
                return False

        def remove(self, flavor_uuid, node_uuid=None):
            if node_uuid is None:
                uri = '{}/*/runtime/*/flavor/{}'.format(self.store.droot, flavor_uuid)
            else:
                uri = '{}/{}/runtime/*/flavor/{}'.format(self.store.droot, node_uuid, flavor_uuid)
            res = self.store.desired.remove(uri)
            if res:
                return True
            else:
                return False

        def search(self, search_dict, node_uuid=None):
            pass

    '''
    Methods
    
    - manifest
        -check
    - node
        - list
        - info
        - plugins
        - search
    - plugin
        - add
        - remove
        - info
        - list
        - search
    - network
        - add
        - remove
        - list
        - search
    - entity
        - add
        - remove
        - define
        - undefine
        - configure
        - clean
        - run
        - stop
        - pause
        - resume
        - migrate
        - search
    - images
        - add
        - remove 
        - search
    - flavor
        - add
        - remove
        - search

    
    '''
