import sys, os

sys.path.append(os.path.join(sys.path[0].rstrip("tests")))
import unittest


def resolve_dependencies(components):
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
        # print (no_dependable_components)
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


def dot2dict(dot_notation, value=None):
    ld = []

    tokens = dot_notation.split('.')
    n_tokens = len(tokens)
    for i in range(n_tokens, 0, -1):
        if i == n_tokens and value is not None:
            ld.append({tokens[i - 1]: value})
        else:
            ld.append({tokens[i - 1]: ld[-1]})

    return ld[-1]


def args2dict(values):
    data = {}
    uri_values = values.split('&')
    for tokens in uri_values:
        v = tokens.split('=')[-1]
        k = tokens.split('=')[0]
        if len(k.split('.')) < 2:
            data.update({k: v})
        else:
            d = dot2dict(k, v)
            data.update(d)
    return data


class DependenciesTests(unittest.TestCase):
    def test_resolve_dependencies_with_dependable_components(self):
        intput_data = [{'name': 'c1', 'need': ['c2', 'c3']}, {'name': 'c2', 'need': ['c3']},
                       {'name': 'c3', 'need': ['c4']}, {'name': 'c4', 'need': []}, {'name': 'c5', 'need': []}]
        output_data = ['c4', 'c5', 'c3', 'c2', 'c1']
        self.assertEqual(resolve_dependencies(intput_data), output_data)

    def test_resolve_dependencies_with_no_dependable_components(self):
        intput_data = [{'name': 'c4', 'need': []}, {'name': 'c5', 'need': []}, {'name': 'c3', 'need': []},
                       {'name': 'c2', 'need': []}, {'name': 'c1', 'need': []}]
        output_data = ['c4', 'c5', 'c3', 'c2', 'c1']
        self.assertEqual(resolve_dependencies(intput_data), output_data)

    def test_dotnotation_to_dict_conversion(self):
        input_data = "par=1&val2.val3=4"
        output_data = {'par': '1', 'val2': {'val3': '4'}}
        self.assertEqual(args2dict(input_data), output_data)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
