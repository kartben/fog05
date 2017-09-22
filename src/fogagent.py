from PluginLoader import PluginLoader


def main():
    pl = PluginLoader("./plugins")
    pl.getPlugins()
    kvm=pl.locatePlugin('RuntimeKVM')
    if kvm != None:
        kvm=pl.loadPlugin(kvm)
        kvm.run()
    else:
        print("Error on plugin load")



if __name__=='__main__':
    main()

