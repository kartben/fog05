from jsonschema import validate, ValidationError
from fog05 import Schemas
from dstore import Store
from enum import Enum
import re
import uuid
import json
import fnmatch
import time
import urllib3
import requests


class RESTStore(object):
    def __init__(self, root, host, port):
        self.root = root
        self.host = host
        self.port = port


    def get(self, uri):
        endpoint = "http://{}:{}/get/{}".format(self.host, self.port, uri)
        resp = requests.get(endpoint)
        return json.loads(resp.text)

    def resolve(self, uri):
        return self.get(uri)

    def put(self, uri, value):
        endpoint = "http://{}:{}/put/{}".format(self.host, self.port, uri)
        resp = requests.put(endpoint, data={'value': value})
        return json.loads(resp.text)

    def dput(self, uri, value=None):
        if value is None:
            value = self.args2dict(uri.split('#')[-1])
        endpoint = "http://{}:{}/dput/{}".format(self.host, self.port, uri)
        resp = requests.patch(endpoint, data={'value': value})
        return json.loads(resp.text)

    def getAll(self, uri):
        return self.get(uri)

    def resolveAll(self, uri):
        return self.get(uri)

    def remove(self, uri):
        endpoint = "http://{}:{}/remove/{}".format(self.host, self.port, uri)
        resp = requests.delete(endpoint)
        return json.loads(resp.text)

    def dot2dict(self, dot_notation, value=None):
        ld = []

        tokens = dot_notation.split('.')
        n_tokens = len(tokens)
        for i in range(n_tokens, 0, -1):
            if i == n_tokens and value is not None:
                ld.append({tokens[i - 1]: value})
            else:
                ld.append({tokens[i - 1]: ld[-1]})

        return ld[-1]

    def args2dict(self, values):
        data = {}
        uri_values = values.split('&')
        for tokens in uri_values:
            v = tokens.split('=')[-1]
            k = tokens.split('=')[0]
            if len(k.split('.')) < 2:
                data.update({k: v})
            else:
                d = self.dot2dict(k, v)
                data.update(d)
        return data


class FOSRESTStore(object):

    "Helper class to interact with the Store"

    def __init__(self, host, port, aroot, droot):
        self.aroot = aroot
        self.droot = droot
        self.actual = RESTStore(aroot, host, port)
        self.desired = RESTStore(droot, host, port)



    def close(self):
        '''
        Close the store

        :return: None
        '''
        return None



class WebAPI(object):
    '''
        This class allow the interaction with fog05 using simple Python3 API
        Need the distributed store
    '''

    def __init__(self, host, port, sysid=0, store_id="python-api-rest"):

        self.a_root = 'afos://{}'.format(sysid)
        self.d_root = 'dfos://{}'.format(sysid)
        self.store = FOSRESTStore(host, port, self.a_root, self.d_root)

        self.manifest = self.Manifest(self.store)
        self.node = self.Node(self.store)
        self.plugin = self.Plugin(self.store)
        self.network = self.Network(self.store)
        self.entity = self.Entity(self.store)
        self.image = self.Image(self.store)
        self.flavor = self.Flavor(self.store)

    class Manifest(object):
        '''
        This class encapsulates API for manifests

        '''
        def __init__(self, store=None):
            if store is None:
                raise RuntimeError('store cannot be none in API!')
            self.store = store

        def check(self, manifest, manifest_type):
            '''

            This method allow you to check if a manifest is write in the correct way


            :param manifest: a dictionary rapresenting the JSON manifest
            :param manifest_type: the manifest type from API.Manifest.Type
            :return: boolean
            '''
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
            Manifest types
            '''
            ENTITY = 0
            IMAGE = 1
            FLAVOR = 3
            NETWORK = 4
            PLUGIN = 5

    class Node(object):
        '''

        This class encapsulates the command for Node interaction

        '''

        def __init__(self, store=None):
            if store is None:
                raise RuntimeError('store cannot be none in API!')
            self.store = store

        def list(self):
            '''
            Get all nodes in the current system/tenant

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
            :return: a dictionary with all information about the node
            """
            if node_uuid is None:
                return None
            uri = '{}/{}'.format(self.store.aroot, node_uuid)
            infos = self.store.actual.resolve(uri)
            if infos is None:
                return None
            return json.loads(infos)

        def plugins(self, node_uuid):
            '''

            Get the list of plugin installed on the specified node

            :param node_uuid: the uuid of the node you want info
            :return: a list of the plugins installed in the node with detailed informations
            '''
            uri = '{}/{}/plugins'.format(self.store.aroot, node_uuid)
            response = self.store.actual.get(uri)
            if response is not None:
                return json.loads(response).get('plugins')
            else:
                return None

        def search(self, search_dict):
            '''

            Will search for a node that match information provided in the parameter

            :param search_dict: dictionary contains all information to match
            :return: a list of node matching the dictionary
            '''
            pass

    class Plugin(object):
        '''
        This class encapsulates the commands for Plugin interaction

        '''
        def __init__(self, store=None):
            if store is None:
                raise RuntimeError('store cannot be none in API!')
            self.store = store

        def add(self, manifest, node_uuid=None):
            '''

            Add a plugin to a node or to all node in the system/tenant

            :param manifest: the dictionary representing the plugin manifes
            :param node_uuid: optional the node in which add the plugin
            :return: boolean
            '''


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
            '''

            Will remove a plugin for a node or all nodes

            :param plugin_uuid: the plugin you want to remove
            :param node_uuid: optional the node that will remove the plugin
            :return: boolean
            '''
            pass

        def list(self, node_uuid=None):
            '''

            Same as API.Node.Plugins but can work for all node un the system, return a dictionary with key node uuid and value the plugin list

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
            '''

            Will search for a plugin matching the dictionary in a single node or in all nodes

            :param search_dict: dictionary contains all information to match
            :param node_uuid: optional node uuid in which search
            :return: a dictionary with {node_uuid, plugin uuid list} with matches
            '''
            pass

    class Network(object):
        '''

        This class encapsulates the command for Network element interaction

        '''

        def __init__(self, store=None):
            if store is None:
                raise RuntimeError('store cannot be none in API!')
            self.store = store

        def add(self, manifest, node_uuid=None):
            '''

            Add a network element to a node o to all nodes


            :param manifest: dictionary representing the manifest of that network element
            :param node_uuid: optional the node uuid in which add the network element
            :return: boolean
            '''


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
            '''

            Remove a network element form one or all nodes

            :param net_uuid: uuid of the network you want to remove
            :param node_uuid: optional node from which remove the network element
            :return: boolean
            '''

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
            '''

            List all network element available in the system/teneant or in a specified node

            :param node_uuid: optional node uuid
            :return: dictionary {node uuid: network element list}
            '''

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
            '''

            Will search for a network element matching the dictionary in a single node or in all nodes

            :param search_dict: dictionary contains all information to match
            :param node_uuid: optional node uuid in which search
            :return: a dictionary with {node_uuid, network element uuid list} with matches
            '''
            pass

    class Entity(object):
        '''

        This class encapsulates the api for interaction with entities

        '''

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
                print("handler {}".format(search))
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
                    print("handler {}".format(uuid))
                    return uuid

        def __get_entity_handler_by_type(self, node_uuid, t):
            handler = None
            handler = self.__search_plugin_by_name(t, node_uuid)
            if handler is None:
                print('type not yet supported')
            print("handler {}".format(handler))
            return handler

        def __wait_atomic_entity_state_change(self, node_uuid, handler_uuid, entity_uuid, state):
            while True:
                time.sleep(1)
                uri = '{}/{}/runtime/{}/entity/{}'.format(self.store.aroot, node_uuid, handler_uuid, entity_uuid)
                data = self.store.actual.get(uri)
                if data is not None:
                    entity_info = json.loads(data)
                    if entity_info is not None and entity_info.get('status') == state:
                        return

        def __wait_atomic_entity_instance_state_change(self, node_uuid, handler_uuid, entity_uuid, instance_uuid, state):
            while True:
                time.sleep(1)
                uri = '{}/{}/runtime/{}/entity/{}/instance/{}'.format(self.store.aroot, node_uuid, handler_uuid, entity_uuid, instance_uuid)
                data = self.store.actual.get(uri)
                if data is not None:
                    entity_info = json.loads(data)
                    if entity_info is not None and entity_info.get('status') == state:
                        return

        def add(self, manifest, node_uuid=None, wait=False):
            '''
            define, configure and run an entity all in one shot
            :param manifest: manifest rapresenting the entity
            :param node_uuid: optional uuid of the node in which the entity will be added
            :param wait: flag for wait that everything is started before returing
            :return: the instance uuid
            '''
            pass

        def remove(self, entity_uuid, node_uuid=None, wait=False):
            '''

            stop, clean and undefine entity all in one shot

            :param entity_uuid:
            :param node_uuid:
            :param wait:
            :return: the instance uuid
            '''
            pass

        def define(self, manifest, node_uuid, wait=False):
            '''

            Defines an atomic entity in a node, this method will check the manifest before sending the definition to the node

            :param manifest: dictionary representing the atomic entity manifest
            :param node_uuid: destination node uuid
            :param wait: if wait that the definition is complete before returning
            :return: boolean
            '''

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
                print("Error in manifest {}".format(ve))
                return False

            entity_uuid = manifest.get('uuid')
            entity_definition = manifest
            json_data = json.dumps(entity_definition).replace(' ', '')
            uri = '{}/{}/runtime/{}/entity/{}'.format(self.store.droot, node_uuid, handler.get('uuid'), entity_uuid)

            res = self.store.desired.put(uri, json_data)
            if res:
                if wait:
                    self.__wait_atomic_entity_state_change(node_uuid,handler.get('uuid'), entity_uuid, 'defined')
                return True
            else:
                return False

        def undefine(self, entity_uuid, node_uuid, wait=False):
            '''

            This method undefine an atomic entity in a node

            :param entity_uuid: atomic entity you want to undefine
            :param node_uuid: destination node
            :param wait: if wait before returning that the entity is undefined
            :return: boolean
            '''
            handler = self.__get_entity_handler_by_uuid(node_uuid, entity_uuid)
            uri = '{}/{}/runtime/{}/entity/{}'.format(self.store.droot, node_uuid, handler, entity_uuid)

            res = self.store.desired.remove(uri)
            if res:
                return True
            else:
                return False

        def configure(self, entity_uuid, node_uuid, instance_uuid=None, wait=False):
            '''

            Configure an atomic entity, creation of the instance

            :param entity_uuid: entity you want to configure
            :param node_uuid: destination node
            :param instance_uuid: optional if preset will use that uuid for the atomic entity instance otherwise will generate a new one
            :param wait: optional wait before returning
            :return: intstance uuid or none in case of error
            '''
            handler = self.__get_entity_handler_by_uuid(node_uuid, entity_uuid)
            if instance_uuid is None:
                instance_uuid = '{}'.format(uuid.uuid4())

            uri = '{}/{}/runtime/{}/entity/{}/instance/{}#status=configure'.format(self.store.droot, node_uuid, handler, entity_uuid, instance_uuid)
            res = self.store.desired.dput(uri)
            if res:
                if wait:
                    self.__wait_atomic_entity_instance_state_change(node_uuid, handler, entity_uuid, instance_uuid, 'configured')
                return instance_uuid
            else:
                return None

        def clean(self, entity_uuid, node_uuid, instance_uuid, wait=False):
            '''

            Clean an atomic entity instance, this will destroy the instance

            :param entity_uuid: entity for which you want to clean an instance
            :param node_uuid: destionation node
            :param instance_uuid: instance you want to clean
            :param wait: optional wait before returning
            :return: boolean
            '''
            handler = yield from self.__get_entity_handler_by_uuid(node_uuid, entity_uuid)
            uri = '{}/{}/runtime/{}/entity/{}/instance/{}'.format(self.store.aroot, node_uuid, handler, entity_uuid, instance_uuid)
            res = self.store.desired.remove(uri)
            if res:
                return True
            else:
                return False

        def run(self, entity_uuid, node_uuid, instance_uuid, wait=False):
            '''

            Starting and atomic entity instance

            :param entity_uuid: entity for which you want to run the instance
            :param node_uuid: destination node
            :param instance_uuid: instance you want to start
            :param wait: optional wait before returning
            :return: boolean
            '''
            handler = self.__get_entity_handler_by_uuid(node_uuid, entity_uuid)
            uri = '{}/{}/runtime/{}/entity/{}/instance/{}#status=run'.format(self.store.droot, node_uuid, handler, entity_uuid, instance_uuid)
            res = self.store.desired.dput(uri)
            if res:
                if wait:
                    self.__wait_atomic_entity_instance_state_change(node_uuid, handler, entity_uuid, instance_uuid, 'run')
                return True
            else:
                return False

        def stop(self, entity_uuid, node_uuid, instance_uuid, wait=False):
            '''

            Shutting down an atomic entity instance

            :param entity_uuid: entity for which you want to shutdown the instance
            :param node_uuid: destination node
            :param instance_uuid: instance you want to shutdown
            :param wait: optional wait before returning
            :return: boolean
            '''

            handler = self.__get_entity_handler_by_uuid(node_uuid, entity_uuid)
            uri = '{}/{}/runtime/{}/entity/{}/instance/{}#status=stop'.format(self.store.droot, node_uuid, handler, entity_uuid, instance_uuid)
            res = self.store.desired.dput(uri)
            if res:
                if wait:
                    self.__wait_atomic_entity_instance_state_change(node_uuid, handler, entity_uuid, instance_uuid, 'stop')
                return True
            else:
                return False

        def pause(self, entity_uuid, node_uuid, instance_uuid, wait=False):
            '''

            Pause the exectution of an atomic entity instance

            :param entity_uuid: entity for which you want to pause the instance
            :param node_uuid: destination node
            :param instance_uuid: instance you want to pause
            :param wait: optional wait before returning
            :return: boolean
            '''
            handler = self.__get_entity_handler_by_uuid(node_uuid, entity_uuid)
            uri = '{}/{}/runtime/{}/entity/{}/instance/{}#status=pause'.format(self.store.droot, node_uuid, handler, entity_uuid, instance_uuid)
            res = self.store.desired.dput(uri)
            if res:
                if wait:
                    self.__wait_atomic_entity_instance_state_change(node_uuid, handler, entity_uuid, instance_uuid, 'pause')
                return True
            else:
                return False

        def resume(self, entity_uuid, node_uuid, instance_uuid, wait=False):
            '''

            resume the exectution of an atomic entity instance

            :param entity_uuid: entity for which you want to resume the instance
            :param node_uuid: destination node
            :param instance_uuid: instance you want to resume
            :param wait: optional wait before returning
            :return: boolean
            '''


            handler = self.__get_entity_handler_by_uuid(node_uuid, entity_uuid)
            uri = '{}/{}/runtime/{}/entity/{}/instance/{}#status=resume'.format(self.store.droot, node_uuid, handler, entity_uuid, instance_uuid)
            res = self.store.desired.dput(uri)
            if res:
                if wait:
                    self.__wait_atomic_entity_instance_state_change(node_uuid, handler, entity_uuid, instance_uuid, 'run')
                return True
            else:
                return False

        def migrate(self, entity_uuid, instance_uuid, node_uuid, destination_node_uuid, wait=False):
            '''

            Live migrate an atomic entity instance between two nodes

            The migration is issued when this command is sended, there is a little overhead for the copy of the base image and the disk image


            :param entity_uuid: ntity for which you want to migrate the instance
            :param instance_uuid: instance you want to migrate
            :param node_uuid: source node for the instance
            :param destination_node_uuid: destination node for the instance
            :param wait: optional wait before returning
            :return: boolean
            '''


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
                uri = '{}/{}/runtime/{}/entity/{}/instance/{}'.format(self.store.droot, node_uuid, handler, entity_uuid, instance_uuid)
                res_dest = yield from self.store.desired.dput(uri, json.dumps(entity_info_src).replace(' ', ''))
                if res_dest:
                    if wait:
                        self.__wait_atomic_entity_instance_state_change(destination_node_uuid, destination_handler.get('uuid'), entity_uuid, instance_uuid, 'run')
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
        '''

        This class encapsulates the action on images


        '''
        def __init__(self, store=None):
            if store is None:
                raise RuntimeError('store cannot be none in API!')
            self.store = store

        def add(self, manifest, node_uuid=None):
            '''

            Adding an image to a node or to all nodes

            :param manifest: dictionary representing the manifest for the image
            :param node_uuid: optional node in which add the image
            :return: boolean
            '''
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
            '''

            remove an image for a node or all nodes

            :param image_uuid: image you want to remove
            :param node_uuid: optional node from which remove the image
            :return: boolean
            '''

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
        '''
          This class encapsulates the action on flavors

        '''
        def __init__(self, store=None):
            if store is None:
                raise RuntimeError('store cannot be none in API!')
            self.store = store

        def add(self, manifest, node_uuid=None):
            '''

            Add a computing flavor to a node or all nodes

            :param manifest: dictionary representing the manifest for the flavor
            :param node_uuid: optional node in which add the flavor
            :return: boolean
            '''
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
            '''

            Remove a flavor from all nodes or a specified node

            :param flavor_uuid: flavor to remove
            :param node_uuid: optional node from which remove the flavor
            :return: boolean
            '''
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

        def list(self, node_uuid=None):
            '''

            List all network element available in the system/teneant or in a specified node

            :param node_uuid: optional node uuid
            :return: dictionary {node uuid: network element list}
            '''

            if node_uuid is not None:
                f_list = []
                uri = '{}/{}/runtime/*/flavor/'.format(self.store.aroot, node_uuid)
                response = self.store.actual.resolveAll(uri)
                for i in response:
                    f_list.append(json.loads(i[1]))
                return {node_uuid: f_list}

            flavs = {}
            uri = '{}/*/runtime/*/flavor/'.format(self.store.aroot)
            response = self.store.actual.resolveAll(uri)
            for i in response:
                id = i[0].split('/')[2]
                net = json.loads(i[1])
                flavs_list = flavs.get(id, None)
                if flavs_list is None:
                    flavs_list = []
                flavs_list.append(net)
                flavs.update({id: flavs_list})
            return flavs

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
