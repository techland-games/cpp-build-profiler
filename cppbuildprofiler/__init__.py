# Copyright (c) Techland. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.

"""
This module contains all code for the cpp-build-profiler utility. Although it
may be used via the parse_vs_log function and Analyser and DependencyGraph
classes, probably the easiest way to use it is to execute the module itself
and perform the profiling interactively via the command line.
"""

from cppbuildprofiler.analysis import Analyser
from cppbuildprofiler.dependency import DependencyGraph
from cppbuildprofiler.parser import parse_vs_log

__all__ = [
    'Analyser',
    'DependencyGraph',
    'parse_vs_log',
    ]
