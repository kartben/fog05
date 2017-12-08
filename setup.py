#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name='fog05',
    version='0.0.2dev',
    author='ATO',
    packages=['fog05', 'fog05/interfaces'],
    install_requires=['networkx', 'jsonschema', 'python-daemon'],
    #install_requires=['networkx', 'jsonschema', 'python-daemon', 'pydds'],
    scripts=['bin/fos', 'bin/fos2', 'bin/fos-get'],
    include_package_data=True
)
