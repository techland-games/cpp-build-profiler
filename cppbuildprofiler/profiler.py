#!/usr/bin/env python

import logging
import os
import argparse
import functools
from cppbuildprofiler.analysis import Analyser
from cppbuildprofiler.dependency import unify_path
from cppbuildprofiler.parser import parse_vs_log

def _is_thirdparty_dependency(dependency_graph, codebase_root, parent, _):
    parent_path = dependency_graph.get_attribute(parent,
                                                 Analyser.ABSOLUTE_PATH_KEY,
                                                 codebase_root)
    return os.path.commonprefix([parent_path, codebase_root]) != codebase_root

def _profile(profile_dir, log_file, codebase_dir, column_separator):
    log_path = os.path.join(profile_dir, log_file)
    logging.info('Parsing %s', log_path)
    depgraph = parse_vs_log(log_path)
    analyser = Analyser(depgraph)

    orig_nodes = depgraph.number_of_nodes()
    orig_edges = depgraph.number_of_edges()
    logging.info('Built dependency graph with %d nodes and %d edges',
                 orig_nodes,
                 orig_edges)

    logging.info('Running analysis...')
    analyser.run_full_analysis()

    logging.info('Removing third-party dependencies')
    codebase_dir = unify_path(codebase_dir)
    depgraph.remove_dependency_by_predicate(
        functools.partial(_is_thirdparty_dependency, depgraph, codebase_dir))
    depgraph.remove_orphans()
    logging.info('Cleanup done. Dependency graph now has %d nodes and %d edges '
                 '(%d nodes and %d edges removed)',
                 depgraph.number_of_nodes(),
                 depgraph.number_of_edges(),
                 orig_nodes - depgraph.number_of_nodes(),
                 orig_edges - depgraph.number_of_edges())

    gml_path = os.path.join(profile_dir, 'graph.gml')
    logging.info('Storing the graph in %s', gml_path)
    depgraph.write(gml_path)

    csv_path = os.path.join(profile_dir, 'stats.csv')
    logging.info('Storing stats in %s', csv_path)
    with open(csv_path, 'w') as f:
        columns = { key: value for (key, value)
                   in Analyser.CSV_COLUMNS.items()
                   if key != Analyser.COMPILATION_COMMAND_KEY }
        depgraph.print_csv(f, columns, column_separator)

def main(args=None):
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser('')
    parser.add_argument(
        'profile_dir',
        action='store',
        help='path to the directory with profiling data')
    parser.add_argument(
        '--log-file', '-l',
        default='log.txt',
        action='store',
        help='Path to the build log file to parse. If relative, assuming child '
             'of profile_dir. Only Visual Studio logs are supported at the moment '
             '(defaults to "log.txt")')
    parser.add_argument(
        '--codebase-dir', '-c',
        action='store',
        required=True,
        help='path to the directory containing first-party code. Files '
             'outside of this directory will be considered third-party '
             'and will have their dependencies removed from the report.'
        )
    parser.add_argument(
        '--column-separator',
        action='store',
        help='column separator (defaults to ";")',
        default=';')

    opts = parser.parse_args(args)

    _profile(opts.profile_dir, opts.log_file, opts.codebase_dir, opts.column_separator)

if __name__ == '__main__':
    main()
