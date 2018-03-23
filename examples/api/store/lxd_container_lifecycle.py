import uuid
from fog05 import API



if __name__ == '__main__':
    api = API()



    container_uuid = '{}'.format(uuid.uuid4())
    container_name = 'example'

    container_definition = {'name': container_name, 'uuid': container_uuid, 'base_image':
        'https://www.dropbox.com/s/7ko6orndmkkekc7/gateway.tar.gz', 'networks': [{
        'br_name': 'lxdbr0', 'intf_name': "eth0"}]}

    entity_manifest = {'name': container_name, 'version': 1, 'entity_data': container_definition, 'type': 'lxd', 'uuid': container_uuid}

    node = api.node.list()
    if len(node) == 0:
        print('No node found aborting!')
        exit(-1)
    else:
        node = node[0][0]

    input('Press enter to define')
    api.entity.define(entity_manifest, node, wait=True)

    input('Press enter to configure')
    instance_uuid = api.entity.configure(container_uuid, node, wait=True)

    input('Press enter to run')
    api.entity.run(container_uuid, node, instance_uuid, wait=True)

    input('Press enter to stop')
    api.entity.stop(container_uuid, node, instance_uuid, wait=True)

    input('Press enter to clean')
    api.entity.clean(container_uuid, node, instance_uuid, wait=True)

    input('Press enter to undefine')
    api.entity.undefine(container_uuid, node, wait=True)

