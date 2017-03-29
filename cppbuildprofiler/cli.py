#!/usr/bin/env python

# Copyright (c) Techland. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.

"""Contains a command line interpreter (CLI) for C++ build profiling."""

import sys
import argparse
import cmd
import os
import logging
import traceback
import functools
import networkx as nx
from cppbuildprofiler import *

class Interpreter(cmd.Cmd):
    
    """
    Implements the command line interpreter.
    """

    _ALL_METRICS = [
        Analyser.Attributes.PROJECT,
        Analyser.Attributes.ABSOLUTE_PATH,
        Analyser.Attributes.TRANSLATION_UNITS,
        Analyser.Attributes.FILE_SIZE,
        Analyser.Attributes.TOTAL_SIZE,
        Analyser.Attributes.BUILD_TIME,
        Analyser.Attributes.AGG_BUILD_TIME_DEV,
        ]

    def __init__(self):
        super().__init__()
        self.prompt = 'c++bp$ '
        self.use_rawinput = True

    def _argv(self, param_string):
        return filter(bool, param_string.split(' '))

    def emptyline(self):
        pass

    def onecmd(self, line):
        try:
            super().onecmd(line)
        except Exception:
            print(traceback.format_exc())

    def do_shell(self, line):
        out = os.popen(line).read()
        print(out)

    def _set_verbosity_argparser(self):
        parser = argparse.ArgumentParser('sets verbosity for the logging '
                                         'system')
        parser.add_argument(
            'level',
            action='store',
            choices=['DEBUG', 'INFO'])
        return parser

    def help_set_verbosity(self):
        self._set_verbosity_argparser().print_help()

    def do_set_verbosity(self, params):
        parser = self._set_verbosity_argparser()
        try:
            opts = parser.parse_args(self._argv(params))
            if opts.level == 'DEBUG':
                logging.getLogger().setLevel(logging.DEBUG)
            elif opts.level == 'INFO':
                logging.getLogger().setLevel(logging.INFO)
        except SystemExit:
            return

    def _get_project_dependency_graph_argparser(self):
        parser = argparse.ArgumentParser('builds a project dependency graph')
        parser.add_argument(
            'path',
            action='store',
            help='path to the file to write to')
        return parser

    def help_get_project_dependency_graph(self):
        self._get_project_dependency_graph_argparser().print_help()

    def do_get_project_dependency_graph(self, params):
        parser = self._get_project_dependency_graph_argparser()
        try:
            opts = parser.parse_args(self._argv(params))
            graph = Analyser(self._depgraph).get_project_dependency_graph()
            nx.write_gml(graph, opts.path)
        except SystemExit:
            return

    def _parse_vs_log_argparser(self):
        parser = argparse.ArgumentParser('parses a visual studio build log '
                                         'and creates a dependency graph')
        parser.add_argument(
            'path',
            action='store',
            help='path to the log file to parse')
        return parser

    def help_parse_vs_log(self):
        self._parse_vs_log_argparser().print_help()

    def do_parse_vs_log(self, params):
        parser = self._parse_vs_log_argparser()
        try:
            opts = parser.parse_args(self._argv(params))
            self._depgraph = parse_vs_log(opts.path)
            logging.info('Parsed %s and created a dependency graph with %d '
                         'nodes and %d edges',
                         opts.path,
                         self._depgraph.number_of_nodes(),
                         self._depgraph.number_of_edges())
        except SystemExit:
            return

    def _load_argparser(self):
        parser = argparse.ArgumentParser('Loads a dependency graph from a file')
        parser.add_argument(
            'path',
            action='store',
            help='path to the file to load from')
        return parser

    def help_load(self):
        self._load_argparser().print_help()

    def do_load(self, params):
        parser = self._load_argparser()
        try:
            opts = parser.parse_args(self._argv(params))
            self._depgraph = DependencyGraph.read(opts.path)
            logging.info('Loaded dependency graph from %s with %d nodes '
                         'and %d edges',
                         opts.path,
                         self._depgraph.number_of_nodes(),
                         self._depgraph.number_of_edges())
        except SystemExit:
            return

    def _store_argparser(self):
        parser = argparse.ArgumentParser('Stores a dependency graph in a file')
        parser.add_argument(
            'path',
            action='store',
            help='path to the file to write to')
        return parser

    def help_store(self):
        self._store_argparser().print_help()

    def do_store(self, params):
        parser = self._store_argparser()
        try:
            opts = parser.parse_args(self._argv(params))
            self._depgraph.write(opts.path)
            logging.info('Stored dependency graph from %s with %d nodes '
                         'and %d edges',
                         opts.path,
                         self._depgraph.number_of_nodes(),
                         self._depgraph.number_of_edges())
        except SystemExit:
            return

    def _analyse_argparser(self):
        parser = argparse.ArgumentParser('runs the dependency graph analysis')
        parser.add_argument(
            '--update-only', '-u',
            action='store_true',
            help='update-only (don\'t re-calculate file size metrics)')
        return parser

    def help_analyse(self):
        self._analyse_argparser().print_help()

    def do_analyse(self, params):
        parser = self._analyse_argparser()
        try:
            opts = parser.parse_args(self._argv(params))
            if opts.update_only:
                Analyser(self._depgraph).update_analysis()
            else:
                Analyser(self._depgraph).run_full_analysis()
        except SystemExit:
            return

    def _remove_thirdparty_dependencies_argparser(self):
        parser = argparse.ArgumentParser('removes third-party header '
                                         'dependencies')
        parser.add_argument(
            'codebase_root',
            action='store',
            help='path to the root directory of the codebase')
        return parser

    def help_remove_thirdparty_dependencies(self):
        self._remove_thirdparty_dependencies_argparser().print_help()

    def _is_thirdparty_dependency(self, codebase_root, parent, child):
        parent_path = self._depgraph.get_attribute(parent,
                                                   Analyser.Attributes.ABSOLUTE_PATH,
                                                   codebase_root)
        return os.path.commonprefix([parent_path, codebase_root]) != codebase_root

    def do_remove_thirdparty_dependencies(self, params):
        try:
            parser = self._remove_thirdparty_dependencies_argparser()
            opts = parser.parse_args(self._argv(params))
            codebase_root = unify_path(opts.codebase_root)

            self._depgraph.remove_dependency_by_predicate(
                functools.partial(self._is_thirdparty_dependency, codebase_root))
            self._depgraph.remove_orphans()
        except SystemExit:
            return

    def _subgraph_argparser(self):
        parser = argparse.ArgumentParser('creates a subgraph of the '
                                         'dependency graph')
        parser.add_argument('--origin', '-o',
                            action='store',
                            help='label of the origin node')
        parser.add_argument('--dependencies', action='store_true',
                            help='include nodes origin depends on')
        parser.add_argument('--dependants', action='store_true',
                            help='include nodes that depend on origin')
        return parser

    def help_subgraph(self):
        self._subgraph_argparser().print_help()

    def do_subgraph(self, params):
        parser = self._subgraph_argparser()
        try:
            opts = parser.parse_args(self._argv(params))
            pre_nodes = self._depgraph.number_of_nodes()
            pre_edges = self._depgraph.number_of_edges()
            self._depgraph = self._depgraph.get_subgraph(opts.origin,
                                                         opts.dependencies,
                                                         opts.dependants)
            logging.info('Created subgraph of %s with %d nodes and %d edges '
                         '(%d nodes and %d edges removed)',
                         opts.origin,
                         self._depgraph.number_of_nodes(),
                         self._depgraph.number_of_edges(),
                         pre_nodes - self._depgraph.number_of_nodes(),
                         pre_edges - self._depgraph.number_of_edges())
        except SystemExit:
            return

    def _print_argparser(self):
        parser = argparse.ArgumentParser('prints the dependency graph')
        parser.add_argument('--out', '-o',
                            action='store',
                            help='file to print out to',
                            required=False)
        parser.add_argument('--nodes', '-n',
                            help='nodes to print',
                            choices=['root', 'top-level', 'dependency'],
                            required=True)
        parser.add_argument('--metrics', '-m',
                            action='store',
                            help='metrics to print (space separated)',
                            nargs='*',
                            choices=self._ALL_METRICS)
        parser.add_argument('--all-metrics', '-M',
                            action='store_const',
                            help='print all available metrics '
                                 '(without the compilation command)',
                            const=self._ALL_METRICS,
                            dest='metrics')
        parser.add_argument('--column-separator',
                            action='store',
                            help='column separator (defaults to ";")',
                            default=';')
        return parser

    def help_print(self):
        self._print_argparser().print_help()

    def do_print(self, params):
        parser = self._print_argparser()
        try:
            opts = parser.parse_args(self._argv(params))

            if opts.metrics is not None:
                metrics = opts.metrics
            else:
                raise RuntimeError('Specify --all-metrics to print all metrics '
                                   'or a list of metrics after --metrics')

            if opts.nodes == 'root':
                available_columns = Analyser.ROOT_COLUMNS
                labels = [DependencyGraph.ROOT_NODE_LABEL]
            elif opts.nodes == 'top-level':
                available_columns = Analyser.TOP_LEVEL_COLUMNS
                labels = self._depgraph.get_top_level_nodes()
            elif opts.nodes == 'dependency':
                available_columns = Analyser.INTERNAL_COLUMNS
                labels = self._depgraph.get_dependency_nodes()
            else:
                assert(False), 'Unexpected nodes value: %s' % opts.nodes

            columns = {metric : available_columns[metric]
                       for metric in metrics if metric in available_columns}

            if opts.out:
                stream = open(opts.out, 'w')
            else:
                stream = os.fdopen(os.dup(sys.stdout.fileno()), 'w')

            with stream:
                self._depgraph.print_csv(
                    stream,
                    columns,
                    opts.column_separator,
                    labels)
        except SystemExit:
            return

    def do_quit(self, params):
        sys.exit(0)

def main(args=None):
    logging.basicConfig(level=logging.INFO)

    if args is None:
        args = sys.argv[1:]

    cl = Interpreter()

    argline = ' '.join(args).strip('\'" \\t')

    if len(argline) > 0:
        for command in argline.split(';'):
            command = command.strip()
            logging.info('Running "%s"', command)
            cl.onecmd(command)
    else:
        cl.cmdloop('Welcome to the C++ build profile command line interface. '
                   'Use "help topic" to print help on a given topic')

if __name__ == '__main__':
    main()
