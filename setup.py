import unittest
import os
from setuptools import setup, find_packages
from distutils.core import Command

HERE = os.path.abspath(os.path.dirname(__file__))
README = os.path.join(HERE, "README.rst")
REQFILE = 'requirements.txt'

classifiers = [
    'License :: OSI Approved :: Apache Software License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.7',
]

with open(README, 'r') as f:
    long_description = f.read()

with open(REQFILE, 'r') as fh:
	dependencies = fh.readlines()

class TestRunner(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        suite = unittest.TestLoader().discover("test")
        t = unittest.TextTestRunner(verbosity=2)
        t.run(suite)

setup(
    name='text_game_maker',
    version='0.6.1',
    description=('Framework for making text-based adventure games (interactive finction)'),
    long_description=long_description,
    url='http://github.com/eriknyquist/text_game_maker',
    author='Erik Nyquist',
    author_email='eknyquist@gmail.com',
    license='Apache 2.0',
    install_requires=dependencies,
    packages=find_packages(exclude=['example-map']),
    package_dir={'text_game_maker':'text_game_maker'},
    package_data={'text_game_maker':['ptttl-data/*.txt', 'utils/*.txt', 'example_map/example_map.json']},
    cmdclass={'test': TestRunner},
    include_package_data=True,
    zip_safe=False
)
