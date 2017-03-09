# Copyright (c) Techland. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.

"""Contains the Analyser class, used to run analysis on the dependency graph."""

import logging
import os
import networkx as nx

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

    PROJECT_KEY = 'project'
    ABSOLUTE_PATH_KEY = 'absolutepath'
    COMPILATION_COMMAND_KEY = 'compilationcommand'
    BUILD_TIME_KEY = 'buildtime'
    FILE_SIZE_KEY = 'filesize'
    TOTAL_SIZE_KEY = 'totalsize'
    TOTAL_BUILD_TIME_KEY = 'totalbuildtime'
    TRANSLATION_UNITS_KEY = 'translationunits'
    TU_BUILD_TIME_TO_SIZE_RATIO = 'tubuildtimetosizeratio'
    UNKNOWN_PROJECT = '__UNKNOWN__'

    CSV_COLUMNS = {
        ABSOLUTE_PATH_KEY: {'title': 'absolute path', 'default': None},
        COMPILATION_COMMAND_KEY: {'title': 'compilation command', 'default': ''},
        BUILD_TIME_KEY: {'title': 'build time [s]', 'default': 0.0},
        FILE_SIZE_KEY: {'title': 'file size [B]', 'default': 0.0},
        TOTAL_SIZE_KEY: {'title': 'total size [B]', 'default': 0.0},
        TOTAL_BUILD_TIME_KEY: {'title': 'total build time of dependants [s]',
                               'default': 0.0},
        TRANSLATION_UNITS_KEY: {'title': 'number of dependent translation units',
                                'default': 0},
        TU_BUILD_TIME_TO_SIZE_RATIO: {'title': 'translation unit build time '
                                               'divided by total size sum [s/B]',
                                      'default': 0},
        }

    def __init__(self, dependency_graph):
        self._dependency_graph = dependency_graph
    
    def _guess_dependency_project(self, label, directory_to_project):
        if self._dependency_graph.has_attribute(label, self.PROJECT_KEY):
            return self._dependency_graph.get_attribute(label, self.PROJECT_KEY)
        directory = os.path.dirname(
            self._dependency_graph.get_attribute(label, self.ABSOLUTE_PATH_KEY))
        while directory not in directory_to_project:
            parent = os.path.dirname(directory)
            if parent == directory:
                return self.UNKNOWN_PROJECT
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
                self._dependency_graph.get_attribute(cpp_node, self.ABSOLUTE_PATH_KEY))
            project = self._dependency_graph.get_attribute(cpp_node, self.PROJECT_KEY)
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
        usage for files pointed to by ABSOLUTE_PATH_KEY in the DependencyGraph.
        """
        logging.info('Calculating file sizes...')
        for label in self._dependency_graph.traverse_post_order():
            path = self._dependency_graph.get_attribute(label,
                                                        self.ABSOLUTE_PATH_KEY)
            file_size = os.path.getsize(path)
            self._dependency_graph.set_attribute(label, self.FILE_SIZE_KEY,
                                                 file_size)
            logging.debug('File size of %s is %s',
                          label, _pretty_filesize(file_size))

    def calculate_total_sizes(self):
        """
        Calculates "total" sizes of files. This is the file size of the node
        plus the sizes of all its dependencies. 
        """
        logging.info('Calculating total sizes...')
        for label in self._dependency_graph.traverse_post_order():
            subtree_size = 0
            subtree = self._dependency_graph.traverse_post_order(label, True)
            for subtree_label in subtree:
                subtree_size += self._dependency_graph.get_attribute(
                    subtree_label, self.FILE_SIZE_KEY)
            self._dependency_graph.set_attribute(label, self.TOTAL_SIZE_KEY,
                                                 subtree_size)
            logging.debug('Total size of %s is %s', label,
                          _pretty_filesize(subtree_size))

    def calculate_total_build_times(self):
        """
        Calculates the "total build time" metric. The total build time for a
        dependency node is the sum of build times of all its dependant top-level
        nodes.
        """
        logging.info('Calculating total build times...')
        for label in self._dependency_graph.get_top_level_nodes():
            build_time = self._dependency_graph.get_attribute(
                label,
                self.BUILD_TIME_KEY)
            subtree = self._dependency_graph.traverse_pre_order(label)
            for subtree_label in subtree:
                current = self._dependency_graph.get_attribute(
                    subtree_label, self.TOTAL_BUILD_TIME_KEY, default=0.0)
                current += build_time
                self._dependency_graph.set_attribute(
                    subtree_label,
                    self.TOTAL_BUILD_TIME_KEY,
                    current)

    def calculate_translation_units(self):
        """
        Calculates the "translation units" metric. The metric value for
        dependency nodes is the number of dependant top-level nodes.
        """
        logging.info('Calculating translation units...')
        for label in self._dependency_graph.get_top_level_nodes():
            subtree = self._dependency_graph.traverse_pre_order(label)
            for subtree_label in subtree:
                current = self._dependency_graph.get_attribute(
                    subtree_label, self.TRANSLATION_UNITS_KEY, default=0)
                current += 1
                self._dependency_graph.set_attribute(
                    subtree_label,
                    self.TRANSLATION_UNITS_KEY,
                    current)

    def calculate_tu_build_time_to_size(self):
        """
        Calculates the "translation unit build time to size ratio" metric.
        The metric value for a dependency node is the sum of all translation
        unit build time divided by total size ratios.
        """
        logging.info('Calculating translation units build time to size ratio...')
        for label in self._dependency_graph.get_top_level_nodes():
            build_time = self._dependency_graph.get_attribute(label, self.BUILD_TIME_KEY)
            total_size = self._dependency_graph.get_attribute(label, self.TOTAL_SIZE_KEY)
            ratio = build_time / total_size
            subtree = self._dependency_graph.traverse_pre_order(label)
            for subtree_label in subtree:
                current = self._dependency_graph.get_attribute(
                    subtree_label, self.TU_BUILD_TIME_TO_SIZE_RATIO, default=0)
                current += ratio
                self._dependency_graph.set_attribute(
                    subtree_label,
                    self.TU_BUILD_TIME_TO_SIZE_RATIO,
                    current)

    def run_full_analysis(self):
        """Calculates all available metrics for the graph"""
        self.calculate_file_sizes()
        self.calculate_total_sizes()
        self.calculate_total_build_times()
        self.calculate_translation_units()
        self.calculate_tu_build_time_to_size()
