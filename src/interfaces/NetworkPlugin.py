from Plugin import Plugin


class NetworkPlugin(Plugin):
    """
    Class: NetworkPlugin

    This class is an interface for plugins that control the network resouces, and provide an abstraction layer
    for networking managment functions
    """

    def __init__(self,version):
        super(NetworkPlugin, self).__init__(version)

    def createVirtualInterface(self, name, uuid):
        """
        This should create a virtual network interface

        :name: String
        :return: tuple (interface_name,interface_uuid) or None in case of failure

        """
        raise NotImplementedError("This is and interface!")
    
    def creareVirtualBridge(self, name, uuid):
        """
        This should create a virtual bridge 

        :name: String
        :return: tuple (bridge_name,bridge_uuid) or None in case of failure
        """
        raise NotImplementedError("This is and interface!")

    def allocateBandwidth(self, intf_uuid, bandwidth):
        """
        This should allocate bandwidth to a certaint virtual interface,
        if the interface not exists throw an exception

        :intf_uuid: String
        :bandwidth: tuple (up,down)
        :return: bool

        """
        raise NotImplementedError("This is and interface!")

    def createVirtualNetwork(self, network_name, uuid, ip_range, has_dhcp, gateway):
        """
        This should create a virtual network, with given caratteristics

        range should specified as CIRD subnet
        eg. 192.168.0.0/24 which means from 192.168.0.1 to 192.168.0.254
        if gateway address is none the entities connected to that network cannot reach internet
        if dhcp is true the easiest way to have a dhcp server is using dnsmasq
        eg. sudo dnsmasq -d  --interface=<bridge_associated_to_this_network> --bind-interfaces  --dhcp-range=<start_ip>,<end_ip>
        using -d you can parse dnsmasq output to listen to events like dhcp ack

        :network_name: String
        :ip_range: String
        :has_dhcp: bool
        :gateway: String
        :return: tuple (net_name,net_uuid) or None in case of failure

        """

        raise NotImplementedError("This is and interface!")

    def assignInterfaceToNetwork(self, network_uuid, intf_uuid):
        """
        This should assign the interface identified by intf_uuid to the network identified by network_uuid,
        if the interface not exists throw an exception

        :network_uuid: String
        :intf_uuid: String
        :return: bool

        """

        raise NotImplementedError("This is and interface!")

    def deleteVirtualInterface(self, intf_uuid):

        """
        This should delete a virtual interface identified by intf_uuid, if the interface is assigned to a network
        maybe can also call removeInterfaceFromNetwork() to avoid any problem,
        if the interface not exists throw an exception

        :intf_uuid: String
        :return: bool

        """

        raise NotImplementedError("This is and interface!")

    def deleteVirtualBridge(self, br_uuid):

        """ 
        Delete a virtual bride, if the bridge is one assigned to a network should throw an exception, if the bridge not exists throw an exception

        :br_uuid: String
        :return: bool
        """

        raise NotImplementedError("This is and interface!")

    def removeInterfaceFromNetwork(self, network_uuid, intf_uuid):

        """
        Remove the interface intf_uuid from network network_uuid, if interface not present throw an exception

        :network_uuid: String
        :intf_uuid: String
        :return: bool

        """

        raise NotImplementedError("This is and interface!")

    def deleteVirtualNetwork(self, network_uuid):

        """
        Delete the virtual network network_uuid, for correct network shutdown should kill the dnsmasq process eventually associated
        for dhcp and remove the bridge, if there are interface associate to this network should throw an exception

        :network_uuid: String
        :return: bool

        """

        raise NotImplementedError("This is and interface!")



class BridgeAssociatedToNetworkException(Exception):
    def __init__(self, message, errors):

        super(BridgeAssociatedToNetworkException, self).__init__(message)
        self.errors = errors


class NetworkHasPendingInterfacesException(Exception):
    def __init__(self, message, errors):

        super(NetworkHasPendingInterfacesException, self).__init__(message)
        self.errors = errors

class InterfaceNotInNetworkException(Exception):
    def __init__(self, message, errors):

        super(InterfaceNotInNetworkException, self).__init__(message)
        self.errors = errors

class BridgeNotExistingException(Exception):
    def __init__(self, message, errors):

        super(BridgeNotExistingException, self).__init__(message)
        self.errors = errors

class InterfaceNotExistingException(Exception):
    def __init__(self, message, errors):

        super(InterfaceNotExistingException, self).__init__(message)
        self.errors = errors