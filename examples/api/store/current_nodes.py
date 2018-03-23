import pprint

from fog05 import API

if __name__ == '__main__':
    api = API()
    pprint.pprint (api.node.list())
