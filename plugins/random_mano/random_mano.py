import sys
import os
import time
import uuid
import json
from random import randint
from fog05.interfaces.MANOPlugin import *



class RandomMANO(MANOPlugin):

    def __init__(self, name, version, agent):
        super(Native, self).__init__(version)
        self.uuid = uuid.uuid4()
        self.name = name
        self.agent = agent
        self.agent.logger.info('__init__()', ' Hello from RandomMano Plugin')
        self.HOME = str("mano/%s" % self.uuid)
        self.startRuntime()

    def onboard_application(self, application_uuid, application_manifest):
        self.logger.info('onboard_application()', ' Onboarding application with uuid: %s' % application_uuid)
        deploy_order_list = self.__resolve_dependencies(application_manifest.get('components', None))
        informations = {}
        '''
        With the ordered list of entities the agent should generate the graph of entities
        eg. using NetworkX lib and looking for loops, if it find a loop should fail the application
        onboarding, and signal in the proper uri.
        If no loop are detected then should start instantiate the components
        It's a MANO job to select the correct nodes, and selection should be based on proximity 
        After each deploy the agent should collect correct information for the deploy of components that need other
        components (eg. should retrive the ip address, and then pass in someway to others components)
        '''

        for c in deploy_order_list:
            search = [x for x in application_manifest.get('components') if x.get('name') == c]
            if len(search) > 0:
                component = search[0]
            else:
                self.logger.warning('onboard_application()',
                                    '[ WARN ] Could not find component in component list WTF?')
                raise AssertionError("Could not find component in component list WTF?")

            '''
            Should recover in some way the component manifest

            '''
            mf = self.__get_manifest(component.get('manifest'))
            '''
            from this manifest generate the correct json 
            '''
            t = mf.get('type')

            if t == "kvm":
                self.logger.info(' Component is a VM')
                kvm = self.__search_plugin_by_name('KVM')
                if kvm is None:
                    self.logger.error('onboard_application()', '[ ERRO ] KVM Plugin not loaded/found!!!')
                    return False

                '''
                Do stuffs... define, configure and run the vm
                get information about the deploy and save them
                eg. {'name':{ information }, 'name2':{}, .... }
                '''

                ## random node selection
                node_uuid = self.__get_node(self.__get_eligible_nodes(self.__get_all_nodes(), mf.get("entity_description")))

                vm_uuid = mf.get("entity_description").get("uuid")

                entity_definition = {'status': 'define', 'name': component.get("name"), 'version': component.get(
                    'version'), 'entity_data': mf.get("entity_description")}
                json_data = json.dumps(entity_definition)

                self.logger.info('onboard_application()', ' Define VM')
                uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s' % (node_uuid, kvm.get('uuid'), vm_uuid))
                self.agent.dstore.put(uri, json_data)

                while True:
                    self.logger.info('onboard_application()', ' Waiting VM to be DEFINED')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, kvm.get('uuid'), vm_uuid))
                    vm_info = json.loads(self.agent.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "defined":
                        break
                self.logger.info('onboard_application()', '[ DONE ] VM DEFINED')

                self.logger.info('onboard_application()', 'Configure VM')
                uri = str(
                    'dfos://<sys-id>/%s/runtime/%s/entity/%s#status=configure' % (node_uuid, kvm.get('uuid'), vm_uuid))
                self.agent.dstore.dput(uri)

                while True:
                    self.logger.info('onboard_application()', 'Waiting VM to be CONFIGURED')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, kvm.get('uuid'), vm_uuid))
                    vm_info = json.loads(self.agent.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "configured":
                        break
                self.logger.info('onboard_application()', '[ DONE ] VM Configured')

                self.logger.info('onboard_application()', 'Staring VM')
                uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s#status=run' % (node_uuid, kvm.get('uuid'), vm_uuid))
                self.agent.dstore.dput(uri)

                while True:
                    self.logger.info('Waiting VM to be RUN')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, kvm.get('uuid'), vm_uuid))
                    vm_info = json.loads(self.agent.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "run":
                        break

                self.logger.info('onboard_application()', '[ DONE ] VM Running on node: %s' % node_uuid)

            elif t == "container":
                self.logger.info('onboard_application()', 'Component is a Container')
                lxd = self.__search_plugin_by_name('KVM')
                if lxd is None:
                    self.logger.error('onboard_application()', '[ ERRO ] LXD Plugin not loaded/found!!!')
                    return False

                node_uuid = self.__get_node(self.__get_eligible_nodes(self.__get_all_nodes(), mf.get("entity_description")))

                container_uuid = mf.get("entity_description").get("uuid")

                entity_definition = {'status': 'define', 'name': component.get("name"), 'version': component.get(
                    'version'), 'entity_data': mf.get("entity_description")}
                json_data = json.dumps(entity_definition)

                self.logger.info('onboard_application()', ' Define container')
                uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s' % (node_uuid, lxd.get('uuid'), container_uuid))
                self.agent.dstore.put(uri, json_data)

                while True:
                    self.logger.info('onboard_application()', ' Waiting container to be DEFINED')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, lxd.get('uuid'), container_uuid))
                    vm_info = json.loads(self.agent.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "defined":
                        break
                self.logger.info('onboard_application()', '[ DONE ] container DEFINED')

                self.logger.info('onboard_application()', 'Configure container')
                uri = str(
                    'dfos://<sys-id>/%s/runtime/%s/entity/%s#status=configure' % (node_uuid, lxd.get('uuid'), container_uuid))
                self.agent.dstore.dput(uri)

                while True:
                    self.logger.info('onboard_application()', 'Waiting container to be CONFIGURED')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, lxd.get('uuid'), container_uuid))
                    vm_info = json.loads(self.agent.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "configured":
                        break
                self.logger.info('onboard_application()', '[ DONE ] container Configured')

                self.logger.info('onboard_application()', 'Staring container')
                uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s#status=run' % (node_uuid, lxd.get('uuid'), container_uuid))
                self.agent.dstore.dput(uri)

                while True:
                    self.logger.info('Waiting container to be RUN')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, lxd.get('uuid'), container_uuid))
                    vm_info = json.loads(self.agent.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "run":
                        break

                self.logger.info('onboard_application()', '[ DONE ] container Running on node: %s' % node_uuid)


            elif t == "native":
                self.logger.info('onboard_application()', 'Component is a Native Application')
                native = self.__search_plugin_by_name('native')
                if native is None:
                    self.logger.error('onboard_application()',
                                      '[ ERRO ] Native Application Plugin not loaded/found!!!')
                    return False

                node_uuid = self.__get_node(self.__get_eligible_nodes(self.__get_all_nodes(), mf.get("entity_description")))
                na_uuid = mf.get("entity_description").get("uuid")

                entity_definition = {'status': 'define', 'name': component.get("name"), 'version': component.get(
                    'version'), 'entity_data': mf.get("entity_description")}
                json_data = json.dumps(entity_definition)

                self.logger.info('onboard_application()', 'Define Native')
                uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s' % (node_uuid, native.get('uuid'), na_uuid))
                self.agent.dstore.put(uri, json_data)

                while True:
                    self.logger.info('onboard_application()', 'Native to be DEFINED')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, native.get('uuid'), na_uuid))
                    vm_info = json.loads(self.agent.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "defined":
                        break
                self.logger.info('onboard_application()', '[ DONE ] Native DEFINED')

                self.logger.info('onboard_application()', ' Configure Native')
                uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s#status=configure' %
                          (node_uuid, native.get('uuid'), na_uuid))
                self.agent.dstore.dput(uri)

                while True:
                    self.logger.info('onboard_application()', 'Native to be CONFIGURED')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, native.get('uuid'), na_uuid))
                    vm_info = json.loads(self.agent.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "configured":
                        break
                self.logger.info('onboard_application()', '[ DONE ] Native CONFIGURED')

                self.logger.info('onboard_application()', 'Starting Native')
                uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s#status=run' %
                          (node_uuid, native.get('uuid'), na_uuid))
                self.agent.dstore.dput(uri)

                while True:
                    self.logger.info('onboard_application()', 'Native to be RUN')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, native.get('uuid'), na_uuid))
                    vm_info = json.loads(self.agent.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "run":
                        break
                self.logger.info('onboard_application()', '[ DONE ] Native Running on node: %s' % node_uuid)

            elif t == "ros2":
                self.logger.info('Component is a ROS2 Application')
                native = self.__search_plugin_by_name('ros2')
                if native is None:
                    self.logger.error('onboard_application()',
                                      '[ ERRO ] ROS2 Application Plugin not loaded/found!!!')
                    return False

                node_uuid = self.__get_node(self.__get_eligible_nodes(self.__get_all_nodes(), mf.get("entity_description")))
                na_uuid = mf.get("entity_description").get("uuid")

                entity_definition = {'status': 'define', 'name': component.get("name"), 'version': component.get(
                    'version'), 'entity_data': mf.get("entity_description")}
                json_data = json.dumps(entity_definition)

                self.logger.info('onboard_application()', 'Define ROS2')
                uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s' % (node_uuid, native.get('uuid'), na_uuid))
                self.agent.dstore.put(uri, json_data)

                while True:
                    self.logger.info('onboard_application()', 'ROS2 to be DEFINED')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, native.get('uuid'), na_uuid))
                    vm_info = json.loads(self.agent.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "defined":
                        break
                self.logger.info('onboard_application()', '[ DONE ] ROS2 DEFINED')

                self.logger.info('onboard_application()', 'Configure Native')
                uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s#status=configure' %
                          (node_uuid, native.get('uuid'), na_uuid))
                self.agent.dstore.dput(uri)

                while True:
                    self.logger.info('onboard_application()', 'ROS2 to be CONFIGURED')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, native.get('uuid'), na_uuid))
                    vm_info = json.loads(self.agent.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "configured":
                        break
                self.logger.info('onboard_application()', '[ DONE ] ROS2 CONFIGURED')

                self.logger.info('onboard_application()', 'Starting ROS2')
                uri = str('dfos://<sys-id>/%s/runtime/%s/entity/%s#status=run' %
                          (node_uuid, native.get('uuid'), na_uuid))
                self.agent.dstore.dput(uri)

                while True:
                    self.logger.info('onboard_application()', 'ROS2 to be RUN')
                    time.sleep(1)
                    uri = str("afos://<sys-id>/%s/runtime/%s/entity/%s" % (node_uuid, native.get('uuid'), na_uuid))
                    vm_info = json.loads(self.agent.astore.get(uri))
                    if vm_info is not None and vm_info.get("status") == "run":
                        break
                self.logger.info('onboard_application()', '[ DONE ] ROS2 Running on node: %s' % node_uuid)

            elif t == "usvc":
                self.logger.info('onboard_application()', 'Component is a Microservice')

            elif t == "application":
                self.logger.info('onboard_application()', 'Component is a Complex Application')
                self.__application_onboarding(mf.get("uuid"), mf.get("entity_description"))

            else:
                self.logger.error('onboard_application()', "Component type not recognized %s" % t)
                raise AssertionError("Component type not recognized %s" % t)


    def offload_application(self, application_uuid):
        raise NotImplemented


    def __resolve_dependencies(self, components):
        '''
        The return list contains component's name in the order that can be used to deploy
         @TODO: should use less cycle to do this job
        :rtype: list
        :param components: list like [{'name': 'c1', 'need': ['c2', 'c3']}, {'name': 'c2', 'need': ['c3']}, {'name': 'c3', 'need': ['c4']}, {'name': 'c4', 'need': []}, {'name': 'c5', 'need': []}]

        no_dependable_components -> list like [[{'name': 'c4', 'need': []}, {'name': 'c5', 'need': []}], [{'name': 'c3', 'need': []}], [{'name': 'c2', 'need': []}], [{'name': 'c1', 'need': []}], []]
        :return: list like ['c4', 'c5', 'c3', 'c2', 'c1']
        '''
        c = list(components)
        no_dependable_components = []
        for i in range(0, len(components)):
            no_dependable_components.append([x for x in c if len(x.get('need')) == 0])
            #print (no_dependable_components)
            c = [x for x in c if x not in no_dependable_components[i]]
            for y in c:
                n = y.get('need')
                n = [x for x in n if x not in [z.get('name') for z in no_dependable_components[i]]]
                y.update({"need": n})

        order = []
        for i in range(0, len(no_dependable_components)):
            n = [x.get('name') for x in no_dependable_components[i]]
            order.extend(n)
        return order

    def __get_manifest(self, manifest_path):
        return json.loads(self.agent.dstore.get(manifest_path))

    def __get_eligible_nodes(self, nodes, entity_manifest):
        eligible = []

        nw_eligible = []
        ac_eligible = []
        io_eligible = []

        constraints = entity_manifest.get("constraints", None)
        if constraints is None:
            return nodes

        arch = constraints.get("arch")
        if arch is not None:
            nodes = [x for x in nodes if x.get('hardware_specifications').get('cpu')[0].get('arch') == arch]

        for node in nodes:
            nw_constraints = constraints.get('networks', None)
            node_nw = node.get('network', None)
            if nw_constraints is not None and node_nw is not None:
                for nw_c in nw_constraints:
                    t = nw_c.get('type')
                    n = nw_c.get('number')
                    nws = [x for x in node_nw if x.get('type') == t and x.get('available') is True]
                    if len(nws) >= n:
                        nw_eligible.append(node.get('uuid'))
            io_constraints = constraints.get('i/o', None)
            node_io = node.get('io', None)
            if io_constraints is not None and node_io is not None:
                for io_c in io_constraints:
                    t = io_c.get('type')
                    n = io_c.get('number')
                    ios = [x for x in node_io if x.get('io_type') == t and x.get('available') is True]
                    if len(ios) >= n:
                        io_eligible.append(node.get('uuid'))
            ac_constraints = constraints.get('accelerators', None)
            node_ac = node.get('accelerator', None)
            if ac_constraints is not None and node_ac is not None:
                node_ac = [x.get('supported_library') for x in node_ac and x.get('available') is True]
                node_sl = []
                for sl in node_ac:
                    node_sl.extend(sl)
                for ac_c in ac_constraints:
                    t = ac_c.get('type')
                    # n = ac_c.get('number')
                    if t in node_sl:
                        ac_eligible.append(node.get('uuid'))
                        # ios = [x for x in node_ac if x.get('type') == t]
                        # if len(ios) >= n:
                        #    ac_elegibles.append(n.get('uuid'))

        if constraints.get('networks', None) is not None and constraints.get('i/o', None) is None and constraints.get(
                'accelerators', None) is None:
            eligible.extend(nw_eligible)
        elif constraints.get('i/o', None) is not None and constraints.get('networks', None) is None and constraints.get(
                'accelerators', None) is None:
            eligible.extend(io_eligible)
        elif constraints.get('accelerators', None) is not None and constraints.get('networks',
                                                                                   None) is None and constraints.get(
                'i/o', None) is None:
            eligible.extend(ac_eligible)
        elif constraints.get('networks', None) is not None and constraints.get('i/o',
                                                                               None) is not None and constraints.get(
                'accelerators', None) is not None:
            eligible = list((set(nw_eligible) & set(io_eligible)) & set(ac_eligible))
        elif constraints.get('networks', None) is not None and constraints.get('i/o',
                                                                               None) is not None and constraints.get(
                'accelerators', None) is None:
            eligible = list(set(nw_eligible) & set(io_eligible))
        elif constraints.get('networks', None) is None and constraints.get('i/o', None) is not None and constraints.get(
                'accelerators', None) is not None:
            eligible = list(set(ac_eligible) & set(io_eligible))
        elif constraints.get('networks', None) is not None and constraints.get('i/o', None) is None and constraints.get(
                'accelerators', None) is not None:
            eligible = list(set(nw_eligible) & set(ac_eligible))
        eligible = list(set(eligible))
        return eligible

    def __get_all_nodes(self):
        uri = str('afos://<sys-id>/*/')
        nodes = json.loads(self.agent.astore.get(uri))
        return nodes

    def __get_node(self, elegible_nodes):
        i = randint(0, len(elegible_nodes))
        return elegible_nodes[i]


