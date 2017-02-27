import logging
import os
import itertools
import networkx as nx
from cppbuildprofiler.analysis import _unify_path

class DependencyGraph:

    _ROOT_NODE_LABEL = '__ROOT__'

    def __init__(self, graph=None):
        if graph is None:
            graph = nx.DiGraph()
        self._graph = graph
        self._graph.add_node(self._ROOT_NODE_LABEL)

    @classmethod
    def read(cls, path):
        result = DependencyGraph()
        result._graph = nx.read_gml(path)
        return result
        
    def write(self, path):
        nx.write_gml(self._graph, path)

    def log_stats(self, prefix):
        logging.info('%s (%d nodes, %d edges)', prefix,
                     self._graph.number_of_nodes(),
                     self._graph.number_of_edges())

    def add_top_level_node(self, label, **kwargs):
        if self._graph.has_node(label):
            raise RuntimeError('Duplicated node for label "%s"' % label)
        self._graph.add_node(label, **kwargs)
        self._graph.add_edge(self._ROOT_NODE_LABEL, label)

    def get_top_level_nodes(self):
        return self._graph.successors_iter(self._ROOT_NODE_LABEL)

    def get_dependent_nodes(self, label):
        return self._graph.predecessors_iter(label)

    def get_node_dependencies(self, label):
        return self._graph.successors_iter(label)

    def get_subgraph(self, label, add_dependencies, add_dependants):
        label = _unify_path(label)
        if not self._graph.has_node(label):
            raise RuntimeError('Node "%s" not found' % label)

        nodes = [label]
        if add_dependencies:
            dependencies = self.traverse_pre_order(label)
            nodes = itertools.chain(nodes, dependencies)
        if add_dependants:
            dependants = self.traverse_pre_order(label, reversed=True)
            nodes = itertools.chain(nodes, dependants)

        return self._graph.subgraph(nodes)

    def has_node(self, label):
        return self._graph.has_node(label)

    def add_dependency_node(self, parent, label, **kwargs):
        if not self._graph.has_node(parent):
            raise RuntimeError('Dependency node parent "%s" not found for label "%s"' %
                (parent, label))
        self._graph.add_node(label, **kwargs)
        self._graph.add_edge(parent, label)

    def remove_dependencies(self, parent):
        if not self._graph.has_node(parent):
            raise RuntimeError('Dependency node parent "%s" not found for label "%s"' %
                (parent, label))
        for child in self._graph.successors(parent):
            logging.debug('Removing %s -> %s dependency', parent, child)
            self._graph.remove_edge(parent, child)

    def remove_nodes(self, labels):
        removed = 0
        for label in labels:
            removed += 1
            logging.debug('Removing %s' % label)
            self._graph.remove_node(label)
        logging.info('Removed %d nodes' % removed)

    def remove_orphans(self):
        pre_nodes = self._graph.number_of_nodes()
        self._graph = self._graph.subgraph(
            nx.dfs_postorder_nodes(self._graph, self._ROOT_NODE_LABEL))
        logging.info('Removed %d orphaned nodes' %
                     (pre_nodes - self._graph.number_of_nodes()))

    def has_attribute(self, label, key):
        return key in self._graph.node[label]

    def get_attribute(self, label, key, default=None):
        if (default is not None) and (key not in self._graph.node[label]):
            return default
        return self._graph.node[label][key]

    def set_attribute(self, label, key, value):
        self._graph.node[label][key] = value

    def _traverse(self, origin, method, include_origin, reversed):
        if not origin:
            origin = self._ROOT_NODE_LABEL
        graph = self._graph
        if reversed:
            graph = nx.reverse(graph)
        nodes = method(graph, origin)
        return (node for node in nodes if node != origin or include_origin)

    def traverse_post_order(self, origin=None, include_origin=False, reversed=False):
        return self._traverse(origin, nx.dfs_postorder_nodes, include_origin, reversed)

    def traverse_pre_order(self, origin=None, include_origin=False, reversed=False):
        return self._traverse(origin, nx.dfs_preorder_nodes, include_origin, reversed)

    def print_csv(self, stream, metrics, column_separator):
        column_separator = column_separator.replace('\\t', '\t')
        column_separator = column_separator.replace('\\n', '\n')

        stream.write('%s%s%s\n' %
                     ('path', column_separator, column_separator.join(metrics)))
        for label in self.traverse_pre_order():
            node = self._graph.node[label]
            stream.write('%s%s%s\n' %
                (label,
                 column_separator,
                 column_separator.join(str(node.get(metric, '')) for metric in metrics)))
