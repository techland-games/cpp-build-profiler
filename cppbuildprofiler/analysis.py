# Copyright (c) Techland. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.

import logging
import os
import re

def _unify_path(path):
    path = os.path.normpath(path)
    path = os.path.normcase(path)
    return path

def _pretty_filesize(size):
    reduced_size = float(size)
    prefixes = [ '', 'K', 'M', 'G' ]
    prefix_idx = 0
    while reduced_size >= 1000.0:
        reduced_size *= 0.001
        prefix_idx += 1
    assert(prefix_idx < len(prefixes)), 'Size is absurd: %s' % size
    return '%0.2f%sB' % (reduced_size, prefixes[prefix_idx])

class Analyser:

    ABSOLUTE_PATH_KEY = 'absolutepath'
    COMPILATION_COMMAND_KEY = 'compilationcommand'
    BUILD_TIME_KEY = 'buildtime'
    FILE_SIZE_KEY = 'filesize'
    TOTAL_SIZE_KEY = 'totalsize'
    TOTAL_BUILD_TIME_KEY = 'totalbuildtime'
    TRANSLATION_UNITS_KEY = 'translationunits'
    TU_BUILD_TIME_TO_SIZE_RATIO = 'tubuildtimetosizeratio'

    def __init__(self, dependency_graph):
        self._dependency_graph = dependency_graph
        
    def calculate_file_sizes(self):
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

    def calculate_translation_units_build_time_to_size_ratio(self):
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

    def remove_pch(self, pattern='_pch.h$'):
        logging.info('Removing pch files...')
        pattern = re.compile(pattern)
        to_remove = list(label for label
                     in self._dependency_graph.traverse_post_order()
                     if len(pattern.findall(label)))
        self._dependency_graph.remove_nodes(to_remove)
        logging.info('Removing orphaned nodes...')
        self._dependency_graph.remove_orphans()

    def remove_thirdparty_dependencies(self, codebase_root):
        logging.info('Removing third-party dependencies...')
        codebase_root = _unify_path(codebase_root)
        thirdparty_parents = list(label for label
            in self._dependency_graph.traverse_post_order()
            if os.path.commonprefix(
                [self._dependency_graph.get_attribute(label, self.ABSOLUTE_PATH_KEY),
                 codebase_root]) != codebase_root)
        for label in thirdparty_parents:
            logging.debug('Removing dependencies of %s', label)
            self._dependency_graph.remove_dependencies(label)
        logging.info('Removing orphaned nodes...')
        self._dependency_graph.remove_orphans()

    def run_full_analysis(self):
        self.calculate_file_sizes()
        self.calculate_total_sizes()
        self.calculate_total_build_times()
        self.calculate_translation_units()
        self.calculate_translation_units_build_time_to_size_ratio()
