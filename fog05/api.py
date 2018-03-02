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

        self.auth = 'a1b2c3d4'

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

        self.a_root = "afos://{}".format(sysid)
        self.d_root = "dfos://{}".format(sysid)
        self.store = FOSStore(self.a_root, self.d_root, 'python-api')

        self.manifest = self.Manifest(self.store)
        self.node = self.Node(self.store)
        self.plugin = self.plugin(self.store)
        self.network = self.network(self.store)
        self.entity = self.entity(self.store)
        self.image = self.image(self.store)
        self.flavor = self.flavor(self.store)

    class Manifest(object):
        def __init__(self, store=None):
            if store is None:
                raise RuntimeError("store cannot be none in API!")
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
                raise RuntimeError("store cannot be none in API!")
            self.store = store

        def list(self):
            pass

        def info(self, node_uuid):
            pass

        def search(self, search_dict):
            pass

    class Plugin(object):
        def __init__(self, store=None):
            if store is None:
                raise RuntimeError("store cannot be none in API!")
            self.store = store

        def add(self, manifest, node_uuid=None):
            pass

        def remove(self, plugin_uuid, node_uuid=None):
            pass

        def list(self, node_uuid=None):
            pass

        def search(self, search_dict, node_uuid=None):
            pass

    class Network(object):
        def __init__(self, store=None):
            if store is None:
                raise RuntimeError("store cannot be none in API!")
            self.store = store

        def add(self, manifest, node_uuid=None):
            pass

        def remove(self, manifest, node_uuid=None):
            pass

        def list(self, node_uuid=None):
            pass

        def search(self, search_dict, node_uuid=None):
            pass

    class Entity(object):
        def __init__(self, store=None):
            if store is None:
                raise RuntimeError("store cannot be none in API!")
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
                raise RuntimeError("store cannot be none in API!")
            self.store = store

        def add(self, manifest, node_uuid=None):
            pass

        def remove(self, image_uuid, node_uuid=None):
            pass

        def search(self, search_dict, node_uuid=None):
            pass

    class Flavor(object):
        def __init__(self, store=None):
            if store is None:
                raise RuntimeError("store cannot be none in API!")
            self.store = store

        def add(self, manifest, node_uuid=None):
            pass

        def remove(self, flavor_uuid, node_uuid=None):
            pass

        def search(self, search_dict, node_uuid=None):
            pass

    '''
    Methods
    
    - manifest
        -check
    - node
        - list
        - info
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
