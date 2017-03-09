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

        a.cpp [file size: 100B, build time: 3.0
        - a.hpp [file size: 10B]
        -- lib.hpp [file size: 20B]
        b.cpp [file size: 30B, build time: 5.0]
        - pch.h [file size: 50B]
        -- lib.hpp [file size: 20B]
        -- other.hpp [file size: 50B]
        '''
        self._files = {}
        self._dependency_graph = DependencyGraph()

        self._dependency_graph.add_top_level_node(
            'a.cpp',
            **{Analyser.BUILD_TIME_KEY: 3.0,
               Analyser.ABSOLUTE_PATH_KEY: self._create_file('a.cpp', 100)})
        self._dependency_graph.add_dependency_node(
            'a.cpp', 'a.hpp',
            **{Analyser.ABSOLUTE_PATH_KEY: self._create_file('a.hpp', 10)})
        libhpp_path = self._create_file('lib.hpp', 20)
        self._dependency_graph.add_dependency_node(
            'a.hpp', 'lib.hpp',
            **{Analyser.ABSOLUTE_PATH_KEY: libhpp_path})

        self._dependency_graph.add_top_level_node(
            'b.cpp',
            **{Analyser.BUILD_TIME_KEY: 5.0,
               Analyser.ABSOLUTE_PATH_KEY: self._create_file('b.cpp', 30)})
        self._dependency_graph.add_dependency_node(
            'b.cpp', 'pch.h',
            **{Analyser.ABSOLUTE_PATH_KEY: self._create_file('pch.h', 50)})
        self._dependency_graph.add_dependency_node(
            'pch.h', 'lib.hpp',
            **{Analyser.ABSOLUTE_PATH_KEY: libhpp_path})
        self._dependency_graph.add_dependency_node(
            'pch.h', 'other.hpp',
            **{Analyser.ABSOLUTE_PATH_KEY: self._create_file('other.hpp', 50)})

    def tearDown(self):
        for output_file in self._files.values():
            os.unlink(output_file)

    def test_individual_file_sizes(self):
        analyser = Analyser(self._dependency_graph)
        analyser.calculate_file_sizes()

        self.assertEqual(
            self._dependency_graph.get_attribute('a.cpp', Analyser.FILE_SIZE_KEY),
            100)
        self.assertEqual(
            self._dependency_graph.get_attribute('a.hpp', Analyser.FILE_SIZE_KEY),
            10)
        self.assertEqual(
            self._dependency_graph.get_attribute('lib.hpp', Analyser.FILE_SIZE_KEY),
            20)
        self.assertEqual(
            self._dependency_graph.get_attribute('b.cpp', Analyser.FILE_SIZE_KEY),
            30)
        self.assertEqual(
            self._dependency_graph.get_attribute('pch.h', Analyser.FILE_SIZE_KEY),
            50)
        self.assertEqual(
            self._dependency_graph.get_attribute('other.hpp', Analyser.FILE_SIZE_KEY),
            50)

    def test_total_file_sizes(self):
        analyser = Analyser(self._dependency_graph)
        analyser.calculate_file_sizes()
        analyser.calculate_total_sizes()

        self.assertEqual(
            self._dependency_graph.get_attribute('a.cpp', Analyser.TOTAL_SIZE_KEY),
            130)
        self.assertEqual(
            self._dependency_graph.get_attribute('a.hpp', Analyser.TOTAL_SIZE_KEY),
            30)
        self.assertEqual(
            self._dependency_graph.get_attribute('lib.hpp', Analyser.TOTAL_SIZE_KEY),
            20)
        self.assertEqual(
            self._dependency_graph.get_attribute('b.cpp', Analyser.TOTAL_SIZE_KEY),
            150)
        self.assertEqual(
            self._dependency_graph.get_attribute('pch.h', Analyser.TOTAL_SIZE_KEY),
            120)
        self.assertEqual(
            self._dependency_graph.get_attribute('other.hpp', Analyser.TOTAL_SIZE_KEY),
            50)

    def test_total_build_times(self):
        analyser = Analyser(self._dependency_graph)
        analyser.calculate_total_build_times()

        self.assertFalse(self._dependency_graph.has_attribute(
            'a.cpp',
            Analyser.TOTAL_BUILD_TIME_KEY))
        self.assertAlmostEqual(
            self._dependency_graph.get_attribute('a.hpp', Analyser.TOTAL_BUILD_TIME_KEY),
            3.0)
        self.assertEqual(
            self._dependency_graph.get_attribute('lib.hpp', Analyser.TOTAL_BUILD_TIME_KEY),
            8.0)
        self.assertFalse(self._dependency_graph.has_attribute(
            'b.cpp',
            Analyser.TOTAL_BUILD_TIME_KEY))
        self.assertEqual(
            self._dependency_graph.get_attribute('pch.h', Analyser.TOTAL_BUILD_TIME_KEY),
            5.0)
        self.assertEqual(
            self._dependency_graph.get_attribute('other.hpp', Analyser.TOTAL_BUILD_TIME_KEY),
            5.0)

    def test_translation_units(self):
        analyser = Analyser(self._dependency_graph)
        analyser.calculate_translation_units()

        self.assertFalse(self._dependency_graph.has_attribute(
            'a.cpp',
            Analyser.TRANSLATION_UNITS_KEY))
        self.assertAlmostEqual(
            self._dependency_graph.get_attribute('a.hpp', Analyser.TRANSLATION_UNITS_KEY),
            1)
        self.assertEqual(
            self._dependency_graph.get_attribute('lib.hpp', Analyser.TRANSLATION_UNITS_KEY),
            2)
        self.assertFalse(self._dependency_graph.has_attribute(
            'b.cpp',
            Analyser.TRANSLATION_UNITS_KEY))
        self.assertEqual(
            self._dependency_graph.get_attribute('pch.h', Analyser.TRANSLATION_UNITS_KEY),
            1)
        self.assertEqual(
            self._dependency_graph.get_attribute('other.hpp', Analyser.TRANSLATION_UNITS_KEY),
            1)

    def test_total_tu_size(self):
        analyser = Analyser(self._dependency_graph)
        analyser.calculate_file_sizes()
        analyser.calculate_total_sizes()
        analyser.calculate_tu_build_time_to_size()

        self.assertFalse(self._dependency_graph.has_attribute(
            'a.cpp',
            Analyser.TU_BUILD_TIME_TO_SIZE_RATIO))
        self.assertAlmostEqual(
            self._dependency_graph.get_attribute('a.hpp', Analyser.TU_BUILD_TIME_TO_SIZE_RATIO),
            3 / 130)
        self.assertEqual(
            self._dependency_graph.get_attribute('lib.hpp', Analyser.TU_BUILD_TIME_TO_SIZE_RATIO),
            (3 / 130) + (5 / 150))
        self.assertFalse(self._dependency_graph.has_attribute(
            'b.cpp',
            Analyser.TU_BUILD_TIME_TO_SIZE_RATIO))
        self.assertEqual(
            self._dependency_graph.get_attribute('pch.h', Analyser.TU_BUILD_TIME_TO_SIZE_RATIO),
            5 / 150)
        self.assertEqual(
            self._dependency_graph.get_attribute('other.hpp', Analyser.TU_BUILD_TIME_TO_SIZE_RATIO),
            5 / 150)

if __name__ == '__main__':
    unittest.main()
