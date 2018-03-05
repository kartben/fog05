from jsonschema import validate, ValidationError
from fog05 import Schemas
from fog05.DStore import *
from enum import Enum


class FOSStore(object):

    def __init__(self, aroot, droot, home):
        self.aroot = aroot  # 'dfos://{}'
        self.ahome = str('{}/{}'.format(aroot, home))  # str('dfos://{}/{}' % self.uuid)

        self.droot = droot  # 'dfos://{}'
        self.dhome = str('{}/{}'.format(droot, home))  # str('dfos://{}/{}' % self.uuid)

        self.actual = DStore('a{}'.format(home), self.aroot, self.ahome, 1024)
        self.desired = DStore('d{}'.format(home), self.droot, self.dhome, 1024)

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
                    validate(manifest, Schemas.app_schema)
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

        def add(self, manifest, node_uuid):
            pass

        def remove(self, entity_uuid, node_uuid):
            pass

        def define(self, entity_uuid, node_uuid):
            pass

        def undefine(self, entity_uuid, node_uuid):
            pass

        def configure(self, entity_uuid, instance_uuid, node_uuid):
            pass

        def clean(self, entity_uuid, instance_uuid, node_uuid):
            pass

        def run(self, entity_uuid, instance_uuid, node_uuid):
            pass

        def stop(self, entity_uuid, instance_uuid, node_uuid):
            pass

        def pause(self, entity_uuid, instance_uuid, node_uuid):
            pass

        def resume(self, entity_uuid, instance_uuid, node_uuid):
            pass

        def migrate(self, entity_uuid, instance_uuid, node_uuid, destination_node_uuid):
            pass

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
