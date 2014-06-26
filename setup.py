#!/usr/bin/env python

from setuptools import setup

with open('pypi.rst') as f:
    long_description = f.read()

setup(name='pylabels',
      version='1.0.1',
      description='Library to generate PDFs for printing labels',
      long_description=long_description,
      author='Blair Bonnett',
      author_email='blair.bonnett@gmail.com',
      url='https://github.com/blairbonnett/pylabels/',
      packages=['labels',],
      requires=['reportlab'],
      provides=['pylabels'],
      license='GPLv3+',
      platforms=['OS Independent'],
      zip_safe=True,
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
      ],
)
