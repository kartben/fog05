#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name='fog05',
    version='0.1.1',
    author='ATO',
    packages=['fog05', 'fog05/interfaces','fog05/svcs'],
    install_requires=['networkx', 'jsonschema', 'python-daemon','websockets'],
    #install_requires=['networkx', 'jsonschema', 'python-daemon', 'pydds'],
    scripts=['bin/fos', 'bin/fos-get','bin/fos.bat', 'bin/fos-get.bat','bin/dstoresvc','bin/f05log.bat',
             'bin/f05log'],
    include_package_data=True
)
