# Copyright (c) Techland. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.

"""
Contains the DependencyGraph class which holds the dependency between compiled
files and their analysis metric values.
"""

import os
import logging
import itertools
from collections import namedtuple
import networkx as nx

def unify_path(path):
    """
    All paths added to the graph should go through this function to make sure
    same paths get stored with the same path string.
    """
    path = os.path.normpath(path)
    path = os.path.normcase(path)
    path = path.replace('\\', '/')
    return path

class DependencyGraph:

    """
    Holds a dependency graph of the compiled files. Top-level nodes, attached
    to the root, are the .cpp files themselves. They connect to internal nodes
    being the files included in the compiled translation unit.
    """

    ROOT_NODE_LABEL = '__ROOT__'

    Column = namedtuple('Column', ['title', 'default_value'])

    def __init__(self, graph=None):
        if graph is None:
            graph = nx.DiGraph()
        self._graph = graph
        self._graph.add_node(self.ROOT_NODE_LABEL)

    @classmethod
    def read(cls, path):
        """
        Reads a .gml file pointed to by the path and returns a DependencyGraph
        constructed from it.
        """
        return DependencyGraph(nx.read_gml(path))
        
    def write(self, path):
        """Writes the dependency graph to a .gml file."""
        nx.write_gml(self._graph, path)

    def number_of_nodes(self):
        """Returns the number of nodes in the dependency graph"""
        return self._graph.number_of_nodes()

    def number_of_edges(self):
        """Returns the number of edges in the dependency graph"""
        return self._graph.number_of_edges()

    def add_top_level_node(self, label, **kwargs):
        """
        Adds a top level node with the provided label and attributes set to the
        provided kwargs. The label must be unique in the graph.
        """
        if self._graph.has_node(label):
            raise RuntimeError('Duplicated node for label "%s"' % label)
        self._graph.add_node(label, **kwargs)
        self._graph.add_edge(self.ROOT_NODE_LABEL, label)

    def add_dependency_node(self, parent, label, **kwargs):
        """
        Adds a dependency node to the graph. If the label is already present,
        only the parent -> label edge is added and the attributes are ignored.
        """
        if not self._graph.has_node(parent):
            raise RuntimeError('Dependency node parent "%s" not found for label "%s"' %
                               (parent, label))
        self._graph.add_node(label, **kwargs)
        self._graph.add_edge(parent, label)

    def has_dependency(self, parent, successor):
        """Returns true iff parent depends on successor (directly or indirectly)"""
        return self._graph.has_node(successor) and nx.has_path(self._graph, parent, successor)

    def get_top_level_nodes(self):
        """Returns an iterator over all the top-level nodes."""
        return self._graph.successors_iter(self.ROOT_NODE_LABEL)

    def get_dependency_nodes(self):
        """Returns an iterator over all internal (dependency) nodes."""
        top_level = frozenset(self.get_top_level_nodes())
        return (label for label in self.traverse_pre_order() if label not in top_level)

    def get_node_immediate_dependencies(self, label):
        """Returns an iterator over the nodes immediate dependencies."""
        return self._graph.successors_iter(label)

    def get_subgraph(self, label, add_dependencies, add_dependants):
        """
        Returns a dependency graph containing the node denoted by the provided
        label. If add_dependants is false, the graph root node is reattached
        to the origin node which becomes the sole top-level node.
        """
        if not self._graph.has_node(label):
            raise RuntimeError('Node "%s" not found' % label)

        nodes = itertools.chain([label])
        if add_dependencies:
            dependencies = self.traverse_pre_order(label)
            nodes = itertools.chain(nodes, dependencies)
        if add_dependants:
            dependants = self.traverse_pre_order(label, reverse=True)
            nodes = itertools.chain(nodes, dependants)

        subgraph = self._graph.subgraph(nodes)

        if not add_dependants:
            subgraph.add_edge(self.ROOT_NODE_LABEL, label)

        return DependencyGraph(subgraph)

    def get_subtree(self, label):
        """Gets the dfs traversal tree with the root at label as a DependencyGraph"""
        subtree = nx.dfs_tree(self._graph, label)
        subtree.add_edge(self.ROOT_NODE_LABEL, label)
        return DependencyGraph(subtree)

    def has_node(self, label):
        """
        Returns True iff a node with the provided label is present in the graph.
        """
        return self._graph.has_node(label)

    def _attribute_matches(self, label, attribute, re_object):
        value = self.get_attribute(label, attribute, None)
        if value is not None:
            return len(re_object.findall(value)) > 0
        else:
            return False

    @classmethod
    def _all_match(cls, label, conditions):
        for condition in conditions:
            if not condition(label):
                return False
        return True

    def remove_dependency_by_predicate(self, predicate):
        """
        Removes dependency edges for which
        predicate(parent_label, dependency_label) evaluates to True.
        """
        for parent in self._graph.nodes_iter():
            if parent != self.ROOT_NODE_LABEL:
                for child in self._graph.successors(parent):
                    if predicate(parent, child):
                        logging.debug('Removing %s -> %s dependency', parent, child)
                        self._graph.remove_edge(parent, child)

    def remove_orphans(self):
        """
        Removes all nodes that are not accessible from the root, i.e. that
        have no dependant top-level nodes.
        """
        pre_nodes = self._graph.number_of_nodes()
        self._graph = self._graph.subgraph(
            nx.dfs_postorder_nodes(self._graph, self.ROOT_NODE_LABEL))
        logging.info('Removed %d orphaned nodes',
                     (pre_nodes - self._graph.number_of_nodes()))

    def has_attribute(self, label, key):
        """Returns True iff the provided label has the given attribute."""
        return key in self._graph.node[label]

    def get_attribute(self, label, key, default=None):
        """
        Returns the attribute value for the provided label. If the attribute is
        not present will return default.
        """
        return self._graph.node[label].get(key, default)

    def set_attribute(self, label, key, value):
        """
        Sets the provided attribute to the given value for the provided label.
        """
        self._graph.node[label][key] = value

    def remove_attribute(self, label, key):
        """
        Removes the given attribute from the label.
        """
        if key in self._graph.node[label]:
            del self._graph.node[label][key]
        
    def _traverse(self, origin, method, include_origin, reverse):
        if not origin:
            origin = self.ROOT_NODE_LABEL
        graph = self._graph
        if reverse:
            graph = nx.reverse(graph)
        nodes = method(graph, origin)
        return (node for node in nodes if node != origin or include_origin)

    def traverse_post_order(self, origin=None, include_origin=False, reverse=False):
        """
        Returns a generator of labels visited post-order starting from the
        origin. If "reverse" is True, the graph edges are reversed (dependency
        to dependant).
        """
        return self._traverse(origin, nx.dfs_postorder_nodes, include_origin, reverse)

    def traverse_pre_order(self, origin=None, include_origin=False, reverse=False):
        """
        Returns a generator of labels visited pre-order starting from the
        origin. If "reverse" is True, the graph edges are reversed (dependency
        to dependant).
        """
        return self._traverse(origin, nx.dfs_preorder_nodes, include_origin, reverse)

    def print_csv(self, stream, columns, column_separator, labels):
        """
        Prints the dependency graph in csv format to the provided stream.

        "columns" is a dictionary, where the keys are the attribute keys,
        and the values are Column objects.
        """
        column_separator = column_separator.replace('\\t', '\t')
        column_separator = column_separator.replace('\\n', '\n')

        stream.write('label%s' % column_separator)
        stream.write('%s\n' % column_separator.join(column.title for column in columns.values()))
        for label in labels:
            node = self._graph.node[label]
            stream.write('%s%s' % (label, column_separator))
            stream.write('%s\n' % 
                         column_separator.join(str(node.get(metric, column.default_value))
                                               for (metric, column) in columns.items()))
