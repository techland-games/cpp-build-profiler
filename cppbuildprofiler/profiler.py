#!/usr/bin/env python

# Copyright (c) Techland. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.

"""
Contains a script executing a typical C++ build profiling session. Generates
a .gml file with the dependency graph for reference and a csv file that could
be imported into a spreadsheet programme for further analysis.
"""

import logging
import os
import argparse
import functools
from cppbuildprofiler.analysis import Analyser
from cppbuildprofiler.dependency import unify_path, DependencyGraph
from cppbuildprofiler.parser import parse_vs_log

def _is_thirdparty_dependency(dependency_graph, codebase_dir, parent, _):
    parent_path = dependency_graph.get_attribute(parent,
                                                 Analyser.Attributes.ABSOLUTE_PATH,
                                                 codebase_dir)
    return os.path.commonprefix([parent_path, codebase_dir]) != codebase_dir

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

    if codebase_dir is not None:
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
    else:
        logging.info('Not removing third-party dependencies, as codebse_dir was not provided')

    gml_path = os.path.join(profile_dir, 'graph.gml')
    logging.info('Storing the graph in %s', gml_path)
    depgraph.write(gml_path)

    root_csv_path = os.path.join(profile_dir, 'root.csv')
    logging.info('Storing root stats in %s', root_csv_path)
    with open(root_csv_path, 'w') as f:
        depgraph.print_csv(f, Analyser.ROOT_COLUMNS, column_separator, [DependencyGraph.ROOT_NODE_LABEL])

    top_level_csv_path = os.path.join(profile_dir, 'top_level.csv')
    logging.info('Storing top_level stats in %s', top_level_csv_path)
    with open(top_level_csv_path, 'w') as f:
        depgraph.print_csv(f, Analyser.TOP_LEVEL_COLUMNS, column_separator, depgraph.get_top_level_nodes())

    dependency_csv_path = os.path.join(profile_dir, 'dependency.csv')
    logging.info('Storing dependency stats in %s', dependency_csv_path)
    with open(dependency_csv_path, 'w') as f:
        depgraph.print_csv(f, Analyser.INTERNAL_COLUMNS, column_separator, depgraph.get_dependency_nodes())

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
        help='path to the directory containing first-party code. Files '
             'outside of this directory will be considered third-party '
             'and will have their dependencies removed from the report.'
        )
    parser.add_argument(
        '--column-separator',
        action='store',
        help='column separator (defaults to ",")',
        default=',')

    opts = parser.parse_args(args)

    _profile(opts.profile_dir, opts.log_file, opts.codebase_dir, opts.column_separator)

if __name__ == '__main__':
    main()
