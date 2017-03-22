#!/usr/bin/env python

# Copyright (c) Techland. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.

import distutils.core
import setuptools

distutils.core.setup(
    name='cppbuildprofiler',
    version='0.2',
    description='A tool that facilitates profiling C++ builds.',
    author='Mikolaj Radwan @ Techland',
    author_email='mikolaj.radwan@techland.pl',
    url='https://github.com/techland-games/cpp-build-profiler',
    download_url='https://github.com/techland-games/cpp-build-profiler/archive/0.1.tar.gz',
    license='MIT',
    packages=['cppbuildprofiler'],
    keywords=['c++', 'building', 'compilation', 'profiling', 'optimisation'],
    entry_points={
        'console_scripts': [
            'cppbuildprofiler-cli = cppbuildprofiler.cli:main',
            'cppbuildprofiler = cppbuildprofiler.profiler:main',
            ]
        },
    install_requires=[
        'networkx',
        ],
    )
