#!/usr/bin/env python

# Copyright (c) Techland. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.

import distutils.core
import setuptools

distutils.core.setup(
    name='cppbuildprofiler',
    version='0.1',
    description='A tool that attempts to facilitate profiling C++ builds.',
    author='Mikolaj Radwan @ Techland',
    author_email='mikolaj.radwan@techland.pl',
    url='https://github.com/techland-games/cpp-build-profiler',
    packages=['cppbuildprofiler'],
    entry_points={
        'console_scripts': [
            'cpp-build-profiler = cppbuildprofiler.__main__:main'
            ]
        }
    )
