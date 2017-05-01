#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

requirements = [
    'pika',
    'twisted',
    # 'tendril',  # Install this manually
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='tendril-monitor-vendor',
    version='0.1.0',
    description="Vendor data maintenance server using Twisted for Tendril",
    long_description=readme,
    author="Chintalagiri Shashank",
    author_email='shashank@chintal.in',
    url='https://github.com/chintal/tendril-monitor-vendor',
    packages=[
        'vendor_monitor',
    ],
    package_dir={'vendor_monitor': 'vendor_monitor'},
    include_package_data=True,
    install_requires=requirements,
    license="MIT",
    zip_safe=False,
    keywords='tendril-monitor-vendor',
    classifiers=[
        'Development Status :: 4 - Beta',
        "License :: OSI Approved :: MIT License",
        'Natural Language :: English',
        'Programming Language :: Python',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
