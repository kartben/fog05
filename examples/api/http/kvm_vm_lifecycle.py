import uuid
from fog05 import WebAPI as API

if __name__ == '__main__':
    api = API('127.0.0.1', 5000)

    vm_uuid = '{}'.format(uuid.uuid4())
    vm_name = 'example_vm'

    vm_definition = {'name': vm_name, 'uuid': vm_uuid, 'cpu': 1, 'memory': 128, 'disk_size': 2, 'base_image':
        'http://download.cirros-cloud.net/0.4.0/cirros-0.4.0-x86_64-disk.img', 'networks': [{
        'mac': "d2:e3:ed:6f:e3:ef", 'br_name': "virbr0"}]}

    entity_manifest = {'status': 'define', 'name': vm_name, 'version': 1, 'entity_data': vm_definition, 'type': 'kvm', 'uuid': vm_uuid}

    node = api.node.list()
    if len(node) == 0:
        print('No node found aborting!')
        exit(-1)
    else:
        node = node[0][0]

    input('Press enter to define')
    if not api.entity.define(entity_manifest, node, wait=True):
        print("Error on define abort...")
        exit(-1)

    input('Press enter to configure')
    instance_uuid = api.entity.configure(vm_uuid, node, wait=True)

    input('Press enter to run')
    api.entity.run(vm_uuid, node, instance_uuid, wait=True)

    input('Press enter to stop')
    api.entity.stop(vm_uuid, node, instance_uuid, wait=True)

    input('Press enter to clean')
    api.entity.clean(vm_uuid, node, instance_uuid, wait=True)

    input('Press enter to undefine')
    api.entity.undefine(vm_uuid, node, wait=True)

