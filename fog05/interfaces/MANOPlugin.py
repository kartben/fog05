from fog05.interfaces import Plugin


class MANOPlugin(Plugin):

    def __init__(self, version):
        super(MANOPlugin, self).__init__(version)

    def onboard_application(self, application_uuid, application_manifest):
        raise NotImplemented

    def offload_application(self, application_uuid):
        raise NotImplemented