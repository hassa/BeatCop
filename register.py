#!/usr/bin/env python
"""
https://coderwall.com/p/qawuyq/use-markdown-readme-s-in-python-modules
"""

from __future__ import print_function

import os


def md_to_rst(md):
    import six
    import pandoc

    # pandoc.core.PANDOC_PATH = '/path/to/pandoc'

    if isinstance(md, six.text_type):
        md = md.encode('utf-8')

    doc = pandoc.Document()
    doc.markdown = md
    result = doc.rst
    if isinstance(result, bytes):
        result = result.decode('utf-8')
    return result


def register_with_rst():
    print("Reading...")
    with open('README.md') as fo:
        md = fo.read()
    print("Converting...")
    rst = md_to_rst(md)
    with open('README.rst', 'w') as fo:
        fo.write(rst)
    return
    print("Registering...")
    try:
        os.system("python setup.py register")
    finally:
        print("Cleanup...")
        os.remove('README.rst')


if __name__ == '__main__':
    register_with_rst()
