import pprint

from fog05 import WebAPI as API

if __name__ == '__main__':
    api = API('127.0.0.1', 5000)
    pprint.pprint (api.node.list())
