#import imp
import importlib
import importlib.machinery
import os
import sys
import pip


class PluginLoader(object):

    def __init__(self, plugin_path):
        self.PluginFolder = plugin_path
        self.MainModule = "__init__"
        self.plugins = []
    
    def get_plugins(self):
        self.plugins = []
        possible_plugins = os.listdir(self.PluginFolder)
        for p in possible_plugins:
            location = os.path.join(self.PluginFolder, p)
            if not os.path.isdir(location) or not '{}.py'.format(self.MainModule) in os.listdir(location):
                continue

            info = os.path.join(location, '{}.py'.format(self.MainModule)) ##importlib.abc.find_module(self.MainModule,
            # [location])
            # #.find_module(
            # self.MainModule,
            # [location])
            self.plugins.append({"name": p, "info": info})
            sys.path.append(os.path.join(sys.path[0], self.PluginFolder, p))
        return self.plugins

    def load_plugin(self, name):

        module = importlib.machinery.SourceFileLoader(name['name'], name['info']).load_module()
        #module = importlib.abc.import_module(self.MainModule,  *name["info"])
        sys.path.append(os.path.abspath(name['info']))
        return module
        #imp.load_module(self.MainModule,)

    def locate_plugin(self, name):
        located = [x for x in self.plugins if x["name"] == name]
        if len(located) > 0:
            return located[0]
        return None

    def install_requirements(self, requirements):
        pip_args = ['install']
        for r in requirements:
            pip_args.append(r)

        pip.main(pip_args)
