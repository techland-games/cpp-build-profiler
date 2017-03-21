# Copyright (c) Techland. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.

import unittest
import tempfile
import os
from cppbuildprofiler import Analyser, DependencyGraph

class TestAnalysis(unittest.TestCase):

    def _create_file(self, prefix, size):
        filename = tempfile.mktemp(prefix=prefix)
        with open(filename, 'w') as output_file:
            output_file.write('.' * size)
        self._files[prefix] = filename
        return filename

    def setUp(self):
        '''
        The test dependency graph is setup as follows:

        pch.cpp [file size: 10B, build time: 10.0, create pch: pch.h]
        - pch.h [file size: 50B]
        -- lib.hpp [file size: 20B]
        a.cpp [file size: 100B, build time: 3.0]
        - other.hpp [file size: 50B]
        - a.hpp [file size: 10B]
        -- lib.hpp [file size: 20B]
        b.cpp [file size: 30B, build time: 5.0, uses pch: pch.h]
        - other.hpp [file size: 50B]
        - pch.h [file size: 50B]
        -- lib.hpp [file size: 20B]
        '''
        self._files = {}
        self._dependency_graph = DependencyGraph()

        self._dependency_graph.add_top_level_node(
            'pch.cpp',
            **{Analyser.Attributes.BUILD_TIME: 10.0,
               Analyser.Attributes.ABSOLUTE_PATH: self._create_file('pch.cpp', 10),
               Analyser.Attributes.CREATED_PCH: 'pch.h'})
        self._dependency_graph.add_dependency_node(
            'pch.cpp', 'pch.h',
            **{Analyser.Attributes.ABSOLUTE_PATH: self._create_file('pch.h', 50)})

        self._dependency_graph.add_top_level_node(
            'a.cpp',
            **{Analyser.Attributes.BUILD_TIME: 3.0,
               Analyser.Attributes.ABSOLUTE_PATH: self._create_file('a.cpp', 100)})
        self._dependency_graph.add_dependency_node(
            'a.cpp', 'other.hpp',
            **{Analyser.Attributes.ABSOLUTE_PATH: self._create_file('other.hpp', 50)})
        self._dependency_graph.add_dependency_node(
            'a.cpp', 'a.hpp',
            **{Analyser.Attributes.ABSOLUTE_PATH: self._create_file('a.hpp', 10)})
        libhpp_path = self._create_file('lib.hpp', 20)
        self._dependency_graph.add_dependency_node(
            'a.hpp', 'lib.hpp',
            **{Analyser.Attributes.ABSOLUTE_PATH: libhpp_path})

        self._dependency_graph.add_top_level_node(
            'b.cpp',
            **{Analyser.Attributes.BUILD_TIME: 5.0,
               Analyser.Attributes.ABSOLUTE_PATH: self._create_file('b.cpp', 30),
               Analyser.Attributes.USED_PCH: 'pch.h'})
        self._dependency_graph.add_dependency_node(
            'b.cpp', 'pch.h',
            **{Analyser.Attributes.ABSOLUTE_PATH: self._create_file('pch.h', 50)})
        self._dependency_graph.add_dependency_node(
            'pch.h', 'lib.hpp',
            **{Analyser.Attributes.ABSOLUTE_PATH: libhpp_path})
        self._dependency_graph.add_dependency_node(
            'b.cpp', 'other.hpp',
            **{Analyser.Attributes.ABSOLUTE_PATH: self._create_file('other.hpp', 50)})

    def tearDown(self):
        for output_file in self._files.values():
            os.unlink(output_file)

    def test_individual_file_sizes(self):
        analyser = Analyser(self._dependency_graph)
        analyser.calculate_file_sizes()

        self.assertEqual(
            self._dependency_graph.get_attribute('pch.cpp', Analyser.Attributes.FILE_SIZE),
            10)
        self.assertEqual(
            self._dependency_graph.get_attribute('pch.h', Analyser.Attributes.FILE_SIZE),
            50)
        self.assertEqual(
            self._dependency_graph.get_attribute('lib.hpp', Analyser.Attributes.FILE_SIZE),
            20)

        self.assertEqual(
            self._dependency_graph.get_attribute('a.cpp', Analyser.Attributes.FILE_SIZE),
            100)
        self.assertEqual(
            self._dependency_graph.get_attribute('a.hpp', Analyser.Attributes.FILE_SIZE),
            10)

        self.assertEqual(
            self._dependency_graph.get_attribute('b.cpp', Analyser.Attributes.FILE_SIZE),
            30)
        self.assertEqual(
            self._dependency_graph.get_attribute('other.hpp', Analyser.Attributes.FILE_SIZE),
            50)

    def test_total_file_sizes(self):
        # adding dependency between b.cpp and a.hpp to check if a.hpp cashes in differently
        # when lib.hpp is added through a pch file
        self._dependency_graph.add_dependency_node('b.cpp', 'a.hpp')

        analyser = Analyser(self._dependency_graph)
        analyser.calculate_file_sizes()
        analyser.calculate_total_sizes()

        self.assertEqual(
            self._dependency_graph.get_attribute('pch.cpp', Analyser.Attributes.TOTAL_SIZE),
            10 + 50 + 20)
        self.assertEqual(
            self._dependency_graph.get_attribute('pch.h', Analyser.Attributes.TOTAL_SIZE),
            50 + 20)
        self.assertEqual(
            self._dependency_graph.get_attribute('lib.hpp', Analyser.Attributes.TOTAL_SIZE),
            20 + 20)

        self.assertEqual(
            self._dependency_graph.get_attribute('a.cpp', Analyser.Attributes.TOTAL_SIZE),
            100 + 10 + 20 + 50)
        self.assertEqual(
            self._dependency_graph.get_attribute('a.hpp', Analyser.Attributes.TOTAL_SIZE),
            10 + 20 + 10)

        self.assertEqual(
            self._dependency_graph.get_attribute('b.cpp', Analyser.Attributes.TOTAL_SIZE),
            30 + 10 + 50) # pch.h and lib.hpp not added
        self.assertEqual(
            self._dependency_graph.get_attribute('other.hpp', Analyser.Attributes.TOTAL_SIZE),
            50 + 50)

    def test_total_build_times(self):
        analyser = Analyser(self._dependency_graph)
        analyser.calculate_total_build_times()

        self.assertFalse(self._dependency_graph.has_attribute(
            'pch.cpp',
            Analyser.Attributes.TOTAL_BUILD_TIME))
        self.assertEqual(
            self._dependency_graph.get_attribute('pch.h', Analyser.Attributes.TOTAL_BUILD_TIME),
            10.0) # b.cpp not added
        self.assertEqual(
            self._dependency_graph.get_attribute('lib.hpp', Analyser.Attributes.TOTAL_BUILD_TIME),
            10.0 + 3.0) # b.cpp not added

        self.assertFalse(self._dependency_graph.has_attribute(
            'a.cpp',
            Analyser.Attributes.TOTAL_BUILD_TIME))
        self.assertAlmostEqual(
            self._dependency_graph.get_attribute('a.hpp', Analyser.Attributes.TOTAL_BUILD_TIME),
            3.0)

        self.assertFalse(self._dependency_graph.has_attribute(
            'b.cpp',
            Analyser.Attributes.TOTAL_BUILD_TIME))
        self.assertEqual(
            self._dependency_graph.get_attribute('other.hpp', Analyser.Attributes.TOTAL_BUILD_TIME),
            3.0 + 5.0)

    def test_translation_units(self):
        analyser = Analyser(self._dependency_graph)
        analyser.calculate_translation_units()

        self.assertFalse(self._dependency_graph.has_attribute(
            'pch.cpp',
            Analyser.Attributes.TRANSLATION_UNITS))
        self.assertEqual(
            self._dependency_graph.get_attribute('pch.h', Analyser.Attributes.TRANSLATION_UNITS),
            1) # b.cpp not added
        self.assertEqual(
            self._dependency_graph.get_attribute('lib.hpp', Analyser.Attributes.TRANSLATION_UNITS),
            2) # b.cpp not added

        self.assertFalse(self._dependency_graph.has_attribute(
            'a.cpp',
            Analyser.Attributes.TRANSLATION_UNITS))
        self.assertAlmostEqual(
            self._dependency_graph.get_attribute('a.hpp', Analyser.Attributes.TRANSLATION_UNITS),
            1)

        self.assertFalse(self._dependency_graph.has_attribute(
            'b.cpp',
            Analyser.Attributes.TRANSLATION_UNITS))
        self.assertEqual(
            self._dependency_graph.get_attribute('other.hpp', Analyser.Attributes.TRANSLATION_UNITS),
            2)

if __name__ == '__main__':
    unittest.main()
