#import imp
import importlib
import os
import sys


class PluginLoader(object):

    def __init__(self, plugin_path):
        self.PluginFolder = plugin_path
        self.MainModule = "__init__"
        self.plugins = []
    
    def getPlugins(self):
        self.plugins = []
        possible_plugins = os.listdir(self.PluginFolder)
        for p in possible_plugins:
            location = os.path.join(self.PluginFolder, p)
            if not os.path.isdir(location) or not self.MainModule + ".py" in os.listdir(location):
                continue

            print(location)
            info = os.path.join(location,self.MainModule + ".py") ##importlib.abc.find_module(self.MainModule,
            # [location])
            # #.find_module(
            # self.MainModule,
            # [location])
            self.plugins.append({"name": p, "info": info})
            sys.path.append(os.path.join(sys.path[0], self.PluginFolder, p))
        return self.plugins

    def loadPlugin(self, name):

        module = importlib.machinery.SourceFileLoader(name['name'], name['info']).load_module()
        #module = importlib.abc.import_module(self.MainModule,  *name["info"])
        return module
        #imp.load_module(self.MainModule,)

    def locatePlugin(self, name):
        located = [x for x in self.plugins if x["name"] == name]
        if len(located) > 0:
            return located[0]
        return None
