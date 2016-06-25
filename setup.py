#!/usr/bin/env python

from setuptools import setup

setup(name='BeatCop',
      version='1.0',
      description='Cluster singleton manager',
      long_description=open('README.md').read(),
      author='??',
      author_email='unspecified@example.com',
      maintainer='HoverHell',
      maintainer_email='hoverhell@gmail.com',
      url='https://github.com/Luluvise/BeatCop',
      requires=['redis(>=2.9.1)'],
      scripts=['beatcop.py'],
)
