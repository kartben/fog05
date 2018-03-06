import json
import pkg_resources
import os
resource_package = 'fog05'  # Could be any module/package name
resource_path = '/'.join(('json_objects', 'network.schema'))


def readFile(file_path):
    with open(file_path, 'r') as f:
        data = f.read()
    return data


network_schema = json.loads(readFile(os.path.join(os.path.dirname(__file__), 'json_objects', 'network.schema')))
atomic_entity_schema = json.loads(readFile(os.path.join(os.path.dirname(__file__), 'json_objects', 'atomic_entity_definition.schema')))
vm_schema = json.loads(readFile(os.path.join(os.path.dirname(__file__), 'json_objects', 'vm.schema')))
native_schema = json.loads(readFile(os.path.join(os.path.dirname(__file__), 'json_objects', 'native_define.schema')))
container_schema = json.loads(readFile(os.path.join(os.path.dirname(__file__), 'json_objects', 'container.schema')))
ros2_schema = json.loads(readFile(os.path.join(os.path.dirname(__file__), 'json_objects', 'ros2_define.schema')))
entity_schema = json.loads(readFile(os.path.join(os.path.dirname(__file__), 'json_objects', 'entity_definition.schema')))