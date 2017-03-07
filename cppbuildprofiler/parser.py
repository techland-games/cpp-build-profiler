# Copyright (c) Techland. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.

import logging
import argparse
import os
import re
import collections
import functools
from cppbuildprofiler.dependency import DependencyGraph
from cppbuildprofiler.analysis import Analyser, _unify_path

_CHANNEL_PATTERN = re.compile(r'^(\d+)>')

class _Channel_state:

    class Node:

        def __init__(self):
            self.label = None
            self.attributes = {}
            self.dependencies = []

        def _update_dependency(self, new_label, dependency):
            parent, child = dependency
            if parent == self.label:
                return (new_label, child)
            else:
                return dependency

        def update_label(self, new_label):
            if self.label != new_label:
                updater = functools.partial(self._update_dependency, new_label)
                self.dependencies = list(map(updater, self.dependencies))
                self.label = new_label

    _PROJECT_PATTERN = re.compile(r'^\d+>[^:]+:\s+Project:\s+([^,]+),')
    _CPP_FILE_PATTERN = re.compile(r'^\d+>\s*(\w+\.c((pp)|(xx))?)')
    _DEPENDENCY_PATTERN = re.compile(r'^\d+>\s*Note: including file:(\s+)(.*)$')
    _TIME_PATTERN = re.compile(r'^\d+>\s*time[^=]+=(\d+\.\d+)s[^\[]+\[([^\]]+)\]')
    _CL_PATTERN = re.compile(r'^\d+>\s*(cl\s+/c[^$]+)$')
    _CL_CPP_FILENAME_PATTERN = re.compile(r'\s(\w[\w/\\]+\.c((pp)|(xx))?)')
    _CPP_EXTENSION_PATTERN = re.compile(r'\.c((pp)|(xx))?$')

    def __init__(self):
        self._project = None
        self._nodes = collections.defaultdict(self.Node)
        self._current_node = None
        self._cl_command = None
        self._cl_files = None

    @classmethod
    def _unique_label(cls, absolute_path, dependency_graph):
        base = os.path.basename(absolute_path)
        suffix = ''
        index = 0
        while dependency_graph.has_node(base + suffix) and \
            dependency_graph.get_attribute(
                    base + suffix, Analyser.ABSOLUTE_PATH_KEY) != absolute_path:
            index += 1
            suffix = '_%d' % index
        return base + suffix

    def _flush(self, dependency_graph):
        for n in self._nodes.values():
            absolute_path = n.label
            n.label = self._unique_label(absolute_path, dependency_graph)
            n.attributes[Analyser.ABSOLUTE_PATH_KEY] = absolute_path
            logging.debug('Adding top level file %s %s',
                          n.label, n.attributes)
            dependency_graph.add_top_level_node(
                n.label,
                **n.attributes)
            for (parent, child) in n.dependencies:
                parent = self._unique_label(parent, dependency_graph)
                child_path = child
                child = self._unique_label(child_path, dependency_graph)
                attributes = {Analyser.ABSOLUTE_PATH_KEY: child_path}
                logging.debug('Adding dependency %s -> %s %s', parent, child, attributes)
                dependency_graph.add_dependency_node(
                    parent,
                    child,
                    **attributes
                    )
        self._nodes.clear()

    def _handle_project_call(self, project, dependency_graph):
        logging.info('Parsing project %s', project)
        self._project = project

    def _handle_cl_call(self, command, dependency_graph):
        self._flush(dependency_graph)

        cl_files = re.findall(self._CL_CPP_FILENAME_PATTERN, command)
        cl_files = list(map(
            lambda m: os.path.basename(_unify_path(m[0])), cl_files))
        self._cl_files = cl_files

        cl_no_files = re.sub(self._CL_CPP_FILENAME_PATTERN, '', command)
        self._cl_command = cl_no_files

    def _handle_cpp_filename(self, filename):
        label = os.path.basename(_unify_path(filename))

        if not self._project:
            raise RuntimeError('Project not set for cpp file %s in channel %d' %
                               filename)

        node = self._nodes[label]
        node.label = label
        node.attributes = {Analyser.PROJECT_KEY: self._project}
        if self._cl_command:
            node.attributes[Analyser.COMPILATION_COMMAND_KEY] = self._cl_command
        self._dependency_stack = [node.label]
        self._current_node = node

        if self._cl_files and label not in self._cl_files:
            raise RuntimeError('Compiled file "%s" not found in cl compiled '
                               'files: %s' % (label, self._cl_files))

    def _handle_dependency(self, depth, dependency_path):
        dependency_path = _unify_path(dependency_path)

        while len(self._dependency_stack) > depth:
            self._dependency_stack.pop()

        parent = self._dependency_stack[-1]
        self._current_node.dependencies.append((parent, dependency_path))
        self._dependency_stack.append(dependency_path)

    def _handle_time(self, build_time, cpp_path):
        cpp_filename = os.path.basename(cpp_path)
        if cpp_filename in self._nodes:
            self._nodes[cpp_path] = self._nodes.pop(cpp_filename)
        
        node = self._nodes[cpp_path]
        node.update_label(cpp_path)

        self._dependency_stack = list(map(
            lambda current: cpp_path if current == cpp_filename else current,
            self._dependency_stack))

        if Analyser.BUILD_TIME_KEY not in node.attributes:
            node.attributes[Analyser.BUILD_TIME_KEY] = 0.0
        node.attributes[Analyser.BUILD_TIME_KEY] += build_time

    def parse_line(self, line, dependency_graph):
        m = self._PROJECT_PATTERN.match(line)
        if m:
            self._handle_project_call(m.group(1), dependency_graph)
            return

        m = self._CL_PATTERN.match(line)
        if m:
            self._handle_cl_call(m.group(1), dependency_graph)
            return

        m = self._CPP_FILE_PATTERN.match(line)
        if m:
            self._handle_cpp_filename(m.group(1))
            return

        m = self._DEPENDENCY_PATTERN.match(line)
        if m:
            self._handle_dependency(len(m.group(1)), m.group(2))
            return

        m = self._TIME_PATTERN.match(line)
        if m:
            self._handle_time(
                float(m.group(1)),
                _unify_path(m.group(2)))
            return

    def end(self, dependency_graph):
        self._flush(dependency_graph)

def parse_vs_log(build_log_path):
    dependency_graph = DependencyGraph()
    channels = collections.defaultdict(_Channel_state)

    with open(build_log_path) as f:
        for l in f:
            l = l.rstrip('\n')
            m = _CHANNEL_PATTERN.match(l)
            if m:
                channel_id = int(m.group(1))
                channels[channel_id].parse_line(l, dependency_graph)

    for c in channels.values():
        c.end(dependency_graph)

    return dependency_graph
