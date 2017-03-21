# Copyright (c) Techland. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.

"""Contains the Analyser class, used to run analysis on the dependency graph."""

import logging
import os
import networkx as nx
from cppbuildprofiler.dependency import DependencyGraph
from collections import defaultdict

def _pretty_filesize(size):
    reduced_size = float(size)
    prefixes = ['', 'K', 'M', 'G']
    prefix_idx = 0
    while reduced_size >= 1000.0:
        reduced_size *= 0.001
        prefix_idx += 1
    assert(prefix_idx < len(prefixes)), 'Size is absurd: %s' % size
    return '%0.2f%sB' % (reduced_size, prefixes[prefix_idx])

class Analyser:
    """Performs an optimisation-related analysis on a dependency graph."""

    class Attributes:
        PROJECT = 'project'
        ABSOLUTE_PATH = 'absolutepath'
        COMPILATION_COMMAND = 'compilationcommand'
        USED_PCH = 'usepch'
        CREATED_PCH = 'createpch'
        BUILD_TIME = 'buildtime'
        FILE_SIZE = 'filesize'
        TOTAL_SIZE = 'totalsize'
        TOTAL_BUILD_TIME = 'totalbuildtime'
        AGG_BUILD_TIME_DEV = 'avgbuildtimedev'
        TRANSLATION_UNITS = 'translationunits'
        TOTAL_TRANSLATION_UNITS = 'totaltranslationunits'
        
    UNKNOWN_PROJECT_NAME = '__UNKNOWN__'

    class Column:
        def __init__(self, title, default_value):
            self.title = title
            self.default_value = default_value

    ROOT_COLUMNS = {
        Attributes.TOTAL_BUILD_TIME: Column('total build time [s]', 0.0),
        Attributes.TOTAL_TRANSLATION_UNITS: Column('total translation units', 0),
        Attributes.TOTAL_SIZE: Column('total size [B]', 0),
        }

    TOP_LEVEL_COLUMNS = {
        Attributes.ABSOLUTE_PATH: Column('absolute path', None),
        Attributes.COMPILATION_COMMAND: Column('compilation command', ''),
        Attributes.BUILD_TIME: Column('build time [s]', 0.0),
        Attributes.FILE_SIZE: Column('file size [B]', 0),
        Attributes.TOTAL_SIZE: Column('total size [B]', 0),
        }

    INTERNAL_COLUMNS = {
        Attributes.ABSOLUTE_PATH: Column('absolute path', None),
        Attributes.TRANSLATION_UNITS: Column('number of dependent translation units', 0),
        Attributes.FILE_SIZE: Column('file size [B]', 0),
        Attributes.TOTAL_SIZE: Column('aggregated total size [B]', 0),
        Attributes.TOTAL_BUILD_TIME: Column('total build time of dependants [s]', 0.0),
        Attributes.AGG_BUILD_TIME_DEV: Column('aggregated build time deviation from avg [s]', 0.0),
        }

    def __init__(self, dependency_graph):
        self._dependency_graph = dependency_graph
        self._build_pch_dependencies()
    
    def _build_pch_dependencies(self):
        self._pch_dependencies = {}
        for cpp_node in self._dependency_graph.get_top_level_nodes():
            create_pch = self._dependency_graph.get_attribute(cpp_node, self.Attributes.CREATED_PCH)
            if create_pch:
                if create_pch in self._pch_dependencies:
                    raise RuntimeError('Duplicate precompiled header name: %s' %
                                       create_pch)
                self._pch_dependencies[create_pch] = frozenset(
                    self._dependency_graph.traverse_pre_order(create_pch, True))

    def _is_pch_dependency(self, parent, child):
        use_pch = self._dependency_graph.get_attribute(parent, self.Attributes.USED_PCH)
        if use_pch:
            return child in self._pch_dependencies[use_pch]
        else:
            return False

    def _guess_dependency_project(self, label, directory_to_project):
        if self._dependency_graph.has_attribute(label, self.Attributes.PROJECT):
            return self._dependency_graph.get_attribute(label, self.Attributes.PROJECT)
        directory = os.path.dirname(
            self._dependency_graph.get_attribute(label, self.Attributes.ABSOLUTE_PATH))
        while directory not in directory_to_project:
            parent = os.path.dirname(directory)
            if parent == directory:
                return self.UNKNOWN_PROJECT_NAME
            else:
                directory = parent
        return directory_to_project[directory]

    def get_project_dependency_graph(self):
        """
        Builds a dependency graph showing relations between projects. This is
        a networkx DiGraph, not a DependencyGraph.
        """
        directory_to_project = {}
        for cpp_node in self._dependency_graph.get_top_level_nodes():
            directory = os.path.dirname(
                self._dependency_graph.get_attribute(cpp_node, self.Attributes.ABSOLUTE_PATH))
            project = self._dependency_graph.get_attribute(cpp_node, self.Attributes.PROJECT)
            if directory in directory_to_project:
                if directory_to_project[directory] != project:
                    logging.error('cpp file %s from project %s in directory %s '
                                  'inconsistent with the currently stored '
                                  'project: %s', cpp_node, project, directory,
                                  directory_to_project[project])
            else:
                directory_to_project[directory] = project

        graph = nx.DiGraph()
        for node in self._dependency_graph.traverse_pre_order():
            dependencies = self._dependency_graph.get_node_immediate_dependencies(node)
            for dependency_node in dependencies:
                source = self._guess_dependency_project(node, directory_to_project)
                target = self._guess_dependency_project(dependency_node, directory_to_project)
                if source != target:
                    graph.add_edge(source, target)
        
        return graph

    def calculate_file_sizes(self):
        """
        Calculates file sizes of individual files by checking the disk
        usage for files pointed to by Metrics.ABSOLUTE_PATH in the DependencyGraph.
        """
        logging.info('Calculating file sizes...')
        for label in self._dependency_graph.traverse_post_order():
            path = self._dependency_graph.get_attribute(label,
                                                        self.Attributes.ABSOLUTE_PATH)
            file_size = os.path.getsize(path)
            self._dependency_graph.set_attribute(label, self.Attributes.FILE_SIZE,
                                                 file_size)
            logging.debug('File size of %s is %s',
                          label, _pretty_filesize(file_size))

    def calculate_total_sizes(self):
        """
        Calculates "total" sizes of files. This is the file size of the node
        plus the sizes of all its dependencies. For top level nodes (.cpp files)
        we're calculating the total size in a straightforward manner. For internal
        nodes we're getting the aggregated subtree total size by summing total
        sizes when included from each of the top level nodes. This is done
        because the subtree size may be significantly smaller if included from
        a file using a precompiled header with one of the subtree nodes.
        """
        logging.info('Calculating total sizes...')
        for label in self._dependency_graph.traverse_pre_order(include_origin=True):
            self._dependency_graph.remove_attribute(label, self.Attributes.TOTAL_SIZE)

        top_level_total_size = 0
        for top_level in self._dependency_graph.get_top_level_nodes():
            subtree_sizes = defaultdict(lambda: 0)
            for internal in self._dependency_graph.traverse_post_order(top_level, True):
                if not self._is_pch_dependency(top_level, internal):
                    subtree_size = self._dependency_graph.get_attribute(internal,
                                                                        self.Attributes.FILE_SIZE)
                    for child in self._dependency_graph.get_node_immediate_dependencies(internal):
                        assert(child in subtree_sizes)
                        subtree_size += subtree_sizes[child]
                    subtree_sizes[internal] += subtree_size
                    current = self._dependency_graph.get_attribute(internal,
                                                                   self.Attributes.TOTAL_SIZE,
                                                                   0)
                    self._dependency_graph.set_attribute(internal,
                                                         self.Attributes.TOTAL_SIZE,
                                                         current + subtree_size)
                else:
                    subtree_sizes[internal] = 0
            top_level_total_size += self._dependency_graph.get_attribute(top_level,
                                                                         self.Attributes.TOTAL_SIZE)

        self._dependency_graph.set_attribute(DependencyGraph.ROOT_NODE_LABEL,
                                             self.Attributes.TOTAL_SIZE,
                                             top_level_total_size)

    def calculate_total_build_times(self):
        """
        Calculates the "total build time" metric. The total build time for a
        dependency node is the sum of build times of all its dependant top-level
        nodes.
        """
        logging.info('Calculating total build times...')
        for label in self._dependency_graph.traverse_post_order():
            self._dependency_graph.remove_attribute(label, self.Attributes.TOTAL_BUILD_TIME)

        total_build_time = 0.0
        for label in self._dependency_graph.get_top_level_nodes():
            build_time = self._dependency_graph.get_attribute(
                label,
                self.Attributes.BUILD_TIME)
            total_build_time += build_time
            subtree = self._dependency_graph.traverse_pre_order(label)
            for subtree_label in subtree:
                if not self._is_pch_dependency(label, subtree_label):
                    current = self._dependency_graph.get_attribute(
                        subtree_label, self.Attributes.TOTAL_BUILD_TIME, default=0.0)
                    current += build_time
                    self._dependency_graph.set_attribute(
                        subtree_label,
                        self.Attributes.TOTAL_BUILD_TIME,
                        current)
        self._dependency_graph.set_attribute(DependencyGraph.ROOT_NODE_LABEL,
                                             self.Attributes.TOTAL_BUILD_TIME,
                                             total_build_time)

    def calculate_translation_units(self):
        """
        Calculates the "translation units" metric. The metric value for
        dependency nodes is the number of dependant top-level nodes.
        """
        logging.info('Calculating translation units...')
        for label in self._dependency_graph.traverse_post_order():
            self._dependency_graph.remove_attribute(label, self.Attributes.TRANSLATION_UNITS)

        total_translation_units = 0
        for label in self._dependency_graph.get_top_level_nodes():
            total_translation_units += 1
            subtree = self._dependency_graph.traverse_pre_order(label)
            for subtree_label in subtree:
                if not self._is_pch_dependency(label, subtree_label):
                    current = self._dependency_graph.get_attribute(
                        subtree_label, self.Attributes.TRANSLATION_UNITS, default=0)
                    current += 1
                    self._dependency_graph.set_attribute(
                        subtree_label,
                        self.Attributes.TRANSLATION_UNITS,
                        current)
        self._dependency_graph.set_attribute(DependencyGraph.ROOT_NODE_LABEL,
                                             self.Attributes.TOTAL_TRANSLATION_UNITS,
                                             0)

    def calculate_agg_build_time_dev(self):
        """
        Calculates the "aggregated build time deviation" metric. This is the sum
        of differences between the average build time and the build time of
        all parents.
        """
        total_build_time = self._dependency_graph.get_attribute(DependencyGraph.ROOT_NODE_LABEL,
                                                                self.Attributes.TOTAL_BUILD_TIME)
        total_tus = self._dependency_graph.get_attribute(DependencyGraph.ROOT_NODE_LABEL,
                                                         self.Attributes.TOTAL_TRANSLATION_UNITS)
        avg_build_time = ((total_build_time / total_tus) if total_tus > 0 else 0)

        for label in self._dependency_graph.traverse_pre_order():
            tus = self._dependency_graph.get_attribute(label, self.Attributes.TOTAL_TRANSLATION_UNITS)
            total_build_time = self._dependency_graph.get_attribute(label,
                                                                    self.Attributes.TOTAL_BUILD_TIME)
            avg_total_build_time = avg_build_time * tus
            self._dependency_graph.set_attribute(label,
                                                 self.Attributes.AGG_BUILD_TIME_DEV,
                                                 total_build_time - avg_total_build_time)

    def run_full_analysis(self):
        """Calculates all available metrics for the graph."""
        self.calculate_file_sizes()
        self.calculate_total_sizes()
        self.calculate_total_build_times()
        self.calculate_translation_units()
        self.calculate_agg_build_time_dev()
