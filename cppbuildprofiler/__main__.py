#!/usr/bin/env python

# Copyright (c) Techland. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.

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

    _ALL_METRICS = [
        Analyser.ABSOLUTE_PATH_KEY,
        Analyser.TRANSLATION_UNITS_KEY,
        Analyser.FILE_SIZE_KEY,
        Analyser.TOTAL_SIZE_KEY,
        Analyser.BUILD_TIME_KEY,
        Analyser.TOTAL_BUILD_TIME_KEY,
        Analyser.TU_BUILD_TIME_TO_SIZE_RATIO,
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
            self._depgraph.log_stats('Parsed %s into a dependency graph' %
                                     opts.path)
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
            self._depgraph.log_stats('Loaded dependency grap from %s' %
                                     opts.path)
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
            self._depgraph.log_stats('Stored dependency graph in %s' %
                                     opts.path)
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
                                                   Analyser.ABSOLUTE_PATH_KEY,
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
            self._depgraph = self._depgraph.get_subgraph(opts.origin,
                                                         opts.dependencies,
                                                         opts.dependants)
            self._depgraph.log_stats('Created subgraph of %s' % opts.origin)
        except SystemExit:
            return

    def _print_argparser(self):
        parser = argparse.ArgumentParser('prints the dependency graph')
        parser.add_argument('--out', '-o',
                            action='store',
                            help='file to print out to',
                            required=False)
        parser.add_argument('--metrics', '-m',
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

            columns = { metric : Analyser.CSV_COLUMNS[metric] for metric in metrics }

            if opts.out:
                stream = open(opts.out, 'w')
            else:
                stream = os.fdopen(os.dup(sys.stdout.fileno()), 'w')

            with stream:
                self._depgraph.print_csv(
                    stream,
                    columns,
                    opts.column_separator)
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
