#!/usr/bin/env python

import sys
import argparse
import cmd
import os
import logging
import traceback
from cppbuildprofiler import *

class Interpreter(cmd.Cmd):

    _CSV_COLUMNS = {
        Analyser.ABSOLUTE_PATH_KEY: { 'title': 'absolute path', 'default': None },
        Analyser.COMPILATION_COMMAND_KEY: { 'title': 'compilation command', 'default': '' },
        Analyser.BUILD_TIME_KEY: { 'title': 'build time [s]', 'default': 0.0 },
        Analyser.FILE_SIZE_KEY: { 'title': 'file size [B]', 'default': 0.0 },
        Analyser.TOTAL_SIZE_KEY: { 'title': 'total size [B]', 'default': 0.0 },
        Analyser.TOTAL_BUILD_TIME_KEY: { 'title': 'total build time of dependants [s]', 'default': 0.0 },
        Analyser.TRANSLATION_UNITS_KEY: { 'title': 'number of dependent translation units', 'default': 0 },
        Analyser.TU_BUILD_TIME_TO_SIZE_RATIO: { 'title': 'translation unit build time divided by total size sum [s/B]', 'default': 0 },
        }

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

    def do_analyse(self, params):
        Analyser(self._depgraph).run_full_analysis()

    def do_remove_pch(self, params):
        Analyser(self._depgraph).remove_pch()

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

    def do_remove_thirdparty_dependencies(self, params):
        try:
            parser = self._remove_thirdparty_dependencies_argparser()
            opts = parser.parse_args(self._argv(params))
            Analyser(self._depgraph).remove_thirdparty_dependencies(
                opts.codebase_root)
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
            self._depgraph = DependencyGraph(self._depgraph.get_subgraph(
                opts.origin, opts.dependencies, opts.dependants))
            self._depgraph.log_stats('Created subgraph of %s' % opts.origin)
        except SystemExit:
            return

    def _print_argparser(self):
        all_metrics = [
            Analyser.ABSOLUTE_PATH_KEY,
            Analyser.TRANSLATION_UNITS_KEY,
            Analyser.FILE_SIZE_KEY,
            Analyser.TOTAL_SIZE_KEY,
            Analyser.BUILD_TIME_KEY,
            Analyser.TOTAL_BUILD_TIME_KEY,
            Analyser.TU_BUILD_TIME_TO_SIZE_RATIO,
            ]
        parser = argparse.ArgumentParser('prints the dependency graph')
        parser.add_argument('--out', '-o',
                            action='store',
                            help='file to print out to',
                            required=False)
        parser.add_argument('--metrics', '-m',
                            help='list of metrics to print',
                            choices=all_metrics)
        parser.add_argument('--all-metrics', '-M',
                            action='store_const',
                            help='print all available metrics '
                                 '(without the compilation command)',
                            const=all_metrics)
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

            if opts.all_metrics:
                metrics = opts.all_metrics
            else:
                metrics = opts.metrics

            columns = { metric : self._CSV_COLUMNS[metric] for metric in metrics }

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
