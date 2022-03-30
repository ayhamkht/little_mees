# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in little_mees/__init__.py
from little_mees import __version__ as version

setup(
	name='little_mees',
	version=version,
	description='Connect Little Mees Dashboard To ERPNext',
	author='Kunhi Mohamed',
	author_email='mohamed@craftinteractive.ae',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
