import sys
import json
from fog05 import API


def read_file(file_path):
    with open(file_path, 'r') as f:
            data = f.read()
    return data



if __name__ == '__main__':

    if len(sys.argv) != 3:
        print("Usage: {} <node_uuid> <path to plugin manifest>")
        exit(-1)

    api = API()
    node_uuid = sys.argv[1]
    manifest_path = sys.argv[2]

    manifest = json.loads(read_file(manifest_path))

    api.plugin.add(manifest, node_uuid)
