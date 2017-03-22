# Copyright (c) Techland. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.

import unittest
import tempfile
import os
from cppbuildprofiler import DependencyGraph

class TestDependency(unittest.TestCase):

    def test_adds_top_level_nodes(self):
        depgraph = DependencyGraph()
        depgraph.add_top_level_node('a.cpp', strattr='value', intattr=2)
        depgraph.add_top_level_node('b.cpp', floatattr=3.5)

        with self.assertRaisesRegex(RuntimeError, 
                                    r'^Duplicated node for label "a\.cpp"'):
            depgraph.add_top_level_node('a.cpp')

        graph = depgraph._graph
        nodes = graph.nodes()
        self.assertEqual(len(nodes), 3)
        self.assertIn(depgraph.ROOT_NODE_LABEL, nodes)
        self.assertIn('a.cpp', nodes)
        self.assertEqual(graph.node['a.cpp']['strattr'], 'value')
        self.assertEqual(graph.node['a.cpp']['intattr'], 2)
        self.assertIn('b.cpp', nodes)
        self.assertEqual(graph.node['b.cpp']['floatattr'], 3.5)

        self.assertEqual(len(graph.edges()), 2)
        self.assertTrue(graph.has_edge(depgraph.ROOT_NODE_LABEL, 'a.cpp'))
        self.assertTrue(graph.has_edge(depgraph.ROOT_NODE_LABEL, 'b.cpp'))

    def test_adds_dependency_nodes(self):
        depgraph = DependencyGraph()
        depgraph.add_top_level_node('a.cpp')
        depgraph.add_dependency_node('a.cpp', 'a.h', intattr=3)
        depgraph.add_dependency_node('a.cpp', 'aa.h')

        depgraph.add_top_level_node('b.cpp', floatattr=3.5)
        depgraph.add_dependency_node('b.cpp', 'b.h')
        depgraph.add_dependency_node('b.h', 'bb.h')
        depgraph.add_dependency_node('b.h', 'a.h', floatattr=1.2)

        with self.assertRaisesRegex(RuntimeError, 
                                    r'Dependency node parent "c.cpp" not found '
                                    r'for label "c.h"'):
            depgraph.add_dependency_node('c.cpp', 'c.h')

        graph = depgraph._graph
        nodes = graph.nodes()
        self.assertEqual(len(nodes), 7)
        self.assertIn(depgraph.ROOT_NODE_LABEL, nodes)
        self.assertIn('a.cpp', nodes)
        self.assertIn('a.h', nodes)
        self.assertEqual(graph.node['a.h']['intattr'], 3)
        self.assertEqual(graph.node['a.h']['floatattr'], 1.2)
        self.assertIn('aa.h', nodes)
        self.assertIn('b.cpp', nodes)
        self.assertIn('b.h', nodes)
        self.assertIn('bb.h', nodes)

        self.assertEqual(len(graph.edges()), 7)
        self.assertTrue(graph.has_edge(depgraph.ROOT_NODE_LABEL, 'a.cpp'))
        self.assertTrue(graph.has_edge(depgraph.ROOT_NODE_LABEL, 'b.cpp'))        
        self.assertTrue(graph.has_edge('a.cpp', 'a.h'))
        self.assertTrue(graph.has_edge('a.cpp', 'aa.h'))
        self.assertTrue(graph.has_edge('b.cpp', 'b.h'))
        self.assertTrue(graph.has_edge('b.h', 'bb.h'))
        self.assertTrue(graph.has_edge('b.h', 'a.h'))

    def test_reads_writes_to_file(self):
        depgraph = DependencyGraph()
        depgraph.add_top_level_node('a.cpp')
        depgraph.add_dependency_node('a.cpp', 'a.h', intattr=3)
        depgraph.add_dependency_node('a.cpp', 'aa.h')

        depgraph.add_top_level_node('b.cpp', floatattr=3.5)
        depgraph.add_dependency_node('b.cpp', 'b.h')
        depgraph.add_dependency_node('b.h', 'bb.h')
        depgraph.add_dependency_node('b.h', 'a.h', floatattr=1.2)

        path = tempfile.mktemp()
        try:
            depgraph.write(path)
            read = depgraph.read(path)
        finally:
            os.remove(path)

        self.assertEqual(
            sorted(depgraph._graph.nodes(data=True)),
            sorted(read._graph.nodes(data=True)))
        self.assertEqual(
            sorted(depgraph._graph.edges(data=True)),
            sorted(read._graph.edges(data=True)))

    def test_attribute_access(self):
        depgraph = DependencyGraph()
        depgraph.add_top_level_node('a.cpp', intattr=0)
        self.assertEqual(depgraph.get_attribute('a.cpp', 'intattr'), 0)
        self.assertFalse(depgraph.has_attribute('a.cpp', 'charattr'))
        self.assertIsNone(depgraph.get_attribute('a.cpp', 'charattr'))
        depgraph.set_attribute('a.cpp', 'charattr', 'a')
        self.assertTrue(depgraph.has_attribute('a.cpp', 'charattr'))
        depgraph.set_attribute('a.cpp', 'intattr', 1)
        self.assertEqual(depgraph.get_attribute('a.cpp', 'intattr'), 1)
        self.assertEqual(depgraph.get_attribute('a.cpp', 'charattr'), 'a')

    def test_removes_dependencies_by_predicate(self):
        depgraph = DependencyGraph()
        depgraph.add_top_level_node('bad-parent')
        depgraph.add_top_level_node('good-parent')
        depgraph.add_dependency_node('bad-parent', 'child-1', good=False)
        depgraph.add_dependency_node('good-parent', 'child-1', good=False)
        depgraph.add_dependency_node('bad-parent', 'child-2', good=True)
        depgraph.add_dependency_node('good-parent', 'child-2', good=False)

        depgraph.remove_dependency_by_predicate(
            lambda parent, child:
            parent == 'bad-parent' and
            depgraph.get_attribute(child, 'good', True) == False)

    def test_subgraph_dependencies(self):
        depgraph = DependencyGraph()
        depgraph.add_top_level_node('a.cpp')
        depgraph.add_dependency_node('a.cpp', 'a.hpp')
        depgraph.add_dependency_node('a.cpp', 'b.hpp')
        depgraph.add_dependency_node('a.cpp', 'c.hpp')
        depgraph.add_dependency_node('b.hpp', 'c.hpp')
        
        subgraph = depgraph.get_subgraph('b.hpp', True, False)

        self.assertEqual(
            sorted(subgraph._graph.nodes()),
            sorted([DependencyGraph.ROOT_NODE_LABEL, 'b.hpp', 'c.hpp']))
        self.assertEqual(
            sorted(subgraph._graph.edges()),
            sorted([(DependencyGraph.ROOT_NODE_LABEL, 'b.hpp'),
                    ('b.hpp', 'c.hpp')]))

if __name__ == '__main__':
    unittest.main()
