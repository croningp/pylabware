from setuptools import setup, find_packages

VERSION = '1.0'
NAME = 'PyLabware'

setup(
    name=NAME,
    version=VERSION,
    install_requires=['pyserial>=3.3', 'pyyaml>=5.0', 'requests>=2.23'],
    package_data={'PyLabware': ['manuals/*']},
    include_package_data=True,
    packages=find_packages(),
    zip_safe=True,
    author='Sergey Zalesskiy',
    author_email='s.zalesskiy@gmail.com',
    license='See LICENSE',
    description='A library to control common chemical laboratory hardware.',
    long_description='',
    platforms=['windows'],
)
