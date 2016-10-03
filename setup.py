#!/usr/bin/env python

from __future__ import print_function

from setuptools import setup


long_description = '...'
for _fln in ('README.rst', 'README.md'):
    try:
        with open(_fln) as fo:
            long_description = fo.read()
    except Exception as exc:
        pass
    else:
        break


setup_kwargs = dict(
    name='BeatCop',
    version='1.0',
    description='Cluster singleton manager',
    long_description=long_description,
    author='??',
    author_email='unspecified@example.com',
    maintainer='HoverHell',
    maintainer_email='hoverhell@gmail.com',
    url='https://github.com/Luluvise/BeatCop',
    requires=['redis(>=2.9.1)'],
    scripts=['beatcop.py'],
)


if __name__ == '__main__':
    setup(**setup_kwargs)
