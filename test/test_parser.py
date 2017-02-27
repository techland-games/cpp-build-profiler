import unittest
import tempfile
import os
from cppbuildprofiler import *

class Test_parser(unittest.TestCase):

    # result of building a project with the following cl options:
    # /Bt+ /showIncludes /nologo- /FC
    _FULL_LOG = r'''
1>------ Rebuild All started: Project: test, Configuration: Debug Win32 ------
2>------ Rebuild All started: Project: test-lib, Configuration: Debug Win32 ------
1>  Microsoft (R) C/C++ Optimizing Compiler Version 19.00.24215.1 for x86
1>  Copyright (C) Microsoft Corporation.  All rights reserved.
1>
1>  cl /c /ZI /nologo /W3 /WX- /Od /Oy- /D WIN32 /D _DEBUG /D _CONSOLE /D _UNICODE /D UNICODE /Gm /EHsc /RTC1 /MDd /GS /fp:precise /Zc:wchar_t /Zc:forScope /Zc:inline /Fo"Debug\\" /Fd"Debug\vc140.pdb" /Gd /TP /analyze- /errorReport:prompt /Bt+ /showIncludes /nologo- /FC test.cpp
1>cl : Command line warning D9035: option 'nologo-' has been deprecated and will be removed in a future release
1>cl : Command line warning D9025: overriding '/nologo' with '/nologo-'
1>
1>  test.cpp
2>  Microsoft (R) C/C++ Optimizing Compiler Version 19.00.24215.1 for x86
2>  Copyright (C) Microsoft Corporation.  All rights reserved.
2>
2>  cl /c /ZI /nologo /W3 /WX- /sdl /Od /Oy- /D WIN32 /D _DEBUG /D _LIB /D _UNICODE /D UNICODE /Gm /EHsc /RTC1 /MDd /GS /fp:precise /Zc:wchar_t /Zc:forScope /Zc:inline /Yc"stdafx.h" /Fp"Debug\test-lib.pch" /Fo"Debug\\" /Fd"Debug\test-lib.pdb" /Gd /TP /analyze- /errorReport:prompt /Bt+ /showIncludes /nologo- /FC stdafx.cpp
2>cl : Command line warning D9035: option 'nologo-' has been deprecated and will be removed in a future release
2>cl : Command line warning D9025: overriding '/nologo' with '/nologo-'
2>
2>  stdafx.cpp
1>  Note: including file: d:\work\test\test\test.hpp
1>  Note: including file: d:\work\test\test\test2.hpp
2>  Note: including file: d:\work\test\test-lib\stdafx.h
2>  Note: including file:  d:\work\test\test-lib\test-lib.hpp
2>  Note: including file:  d:\work\test\test-lib\test-lib2.hpp
1>  time(C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\bin\amd64_x86\c1xx.dll)=0.03792s < 2653389603198 - 2653389729403 > BB [D:\work\test\test\test.cpp]
1>  time(C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\bin\amd64_x86\c2.dll)=0.00622s < 2653389737407 - 2653389758113 > BB [D:\work\test\test\test.cpp]
2>  time(C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\bin\amd64_x86\c1xx.dll)=0.04680s < 2653389639004 - 2653389794759 > BB [D:\work\test\test-lib\stdafx.cpp]
2>  time(C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\bin\amd64_x86\c2.dll)=0.00455s < 2653389801855 - 2653389816992 > BB [D:\work\test\test-lib\stdafx.cpp]
2>  test-lib.vcxproj -> D:\work\test\Debug\test-lib.lib
1>  test.vcxproj -> D:\work\test\Debug\test.exe
1>  test.vcxproj -> D:\work\test\Debug\test.pdb (Full PDB)
========== Rebuild All: 2 succeeded, 0 failed, 0 skipped ==========
'''

    # result of building a project with no extra cl options
    _MINIMAL_LOG = r'''
1>------ Rebuild All started: Project: test, Configuration: Debug Win32 ------
2>------ Rebuild All started: Project: test-lib, Configuration: Debug Win32 ------
1>  test.cpp
2>  stdafx.cpp
2>  test-lib.vcxproj -> D:\work\test\Debug\test-lib.lib
1>  test.vcxproj -> D:\work\test\Debug\test.exe
1>  test.vcxproj -> D:\work\test\Debug\test.pdb (Full PDB)
========== Rebuild All: 2 succeeded, 0 failed, 0 skipped ==========
'''

    _DUPLICATED_LABELS_LOG = r'''
1>------ Rebuild All started: Project: test, Configuration: Debug Win32 ------
2>------ Rebuild All started: Project: test-lib, Configuration: Debug Win32 ------
1>  Microsoft (R) C/C++ Optimizing Compiler Version 19.00.24215.1 for x86
1>  Copyright (C) Microsoft Corporation.  All rights reserved.
1>
1>  cl /c /ZI /nologo /W3 /WX- /Od /Oy- /D WIN32 /D _DEBUG /D _CONSOLE /D _UNICODE /D UNICODE /Gm /EHsc /RTC1 /MDd /GS /fp:precise /Zc:wchar_t /Zc:forScope /Zc:inline /Fo"Debug\\" /Fd"Debug\vc140.pdb" /Gd /TP /analyze- /errorReport:prompt /Bt+ /showIncludes /nologo- /FC test.cpp
1>cl : Command line warning D9035: option 'nologo-' has been deprecated and will be removed in a future release
1>cl : Command line warning D9025: overriding '/nologo' with '/nologo-'
1>
1>  test.cpp
2>  Microsoft (R) C/C++ Optimizing Compiler Version 19.00.24215.1 for x86
2>  Copyright (C) Microsoft Corporation.  All rights reserved.
2>
2>  cl /c /ZI /nologo /W3 /WX- /sdl /Od /Oy- /D WIN32 /D _DEBUG /D _LIB /D _UNICODE /D UNICODE /Gm /EHsc /RTC1 /MDd /GS /fp:precise /Zc:wchar_t /Zc:forScope /Zc:inline /Yc"stdafx.h" /Fp"Debug\test-lib.pch" /Fo"Debug\\" /Fd"Debug\test-lib.pdb" /Gd /TP /analyze- /errorReport:prompt /Bt+ /showIncludes /nologo- /FC test.cpp
2>cl : Command line warning D9035: option 'nologo-' has been deprecated and will be removed in a future release
2>cl : Command line warning D9025: overriding '/nologo' with '/nologo-'
2>
2>  test.cpp
1>  Note: including file: d:\work\test\test\test-same.hpp
1>  Note: including file: d:\work\test\test\test-different.hpp
2>  Note: including file: d:\work\test\test\test-same.hpp
2>  Note: including file: d:\work\test\test-other\test-different.hpp
1>  time(C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\bin\amd64_x86\c1xx.dll)=0.03792s < 2653389603198 - 2653389729403 > BB [D:\work\test\test\test.cpp]
1>  time(C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\bin\amd64_x86\c2.dll)=0.00622s < 2653389737407 - 2653389758113 > BB [D:\work\test\test\test.cpp]
2>  time(C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\bin\amd64_x86\c1xx.dll)=0.04680s < 2653389639004 - 2653389794759 > BB [D:\work\test\test-other\test.cpp]
2>  time(C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\bin\amd64_x86\c2.dll)=0.00455s < 2653389801855 - 2653389816992 > BB [D:\work\test\test-other\test.cpp]
2>  test-lib.vcxproj -> D:\work\test\Debug\test-lib.lib
1>  test.vcxproj -> D:\work\test\Debug\test.exe
1>  test.vcxproj -> D:\work\test\Debug\test.pdb (Full PDB)
========== Rebuild All: 2 succeeded, 0 failed, 0 skipped ==========
'''

    def test_parses_full_vs_log(self):
        log_path = tempfile.mktemp()
        try:
            with open(log_path, 'w') as f:
                f.write(self._FULL_LOG)
            depgraph = parse_vs_log(log_path)

            graph = depgraph._graph
            
            nodes = graph.nodes()
            self.assertEqual(sorted(nodes), sorted([
                depgraph._ROOT_NODE_LABEL,
                'test.cpp',
                'test.hpp',
                'test2.hpp',
                'stdafx.cpp',
                'stdafx.h',
                'test-lib.hpp',
                'test-lib2.hpp',
                ]))

            edges = graph.edges()
            self.assertEqual(sorted(edges), sorted([
                (depgraph._ROOT_NODE_LABEL, 'test.cpp'),
                ('test.cpp', 'test.hpp'),
                ('test.cpp', 'test2.hpp'),
                (depgraph._ROOT_NODE_LABEL, 'stdafx.cpp'),
                ('stdafx.cpp', 'stdafx.h'),
                ('stdafx.h', 'test-lib.hpp'),
                ('stdafx.h', 'test-lib2.hpp'),
                ]))

            test_cpp_node = graph.node['test.cpp']
            self.assertEqual(
                test_cpp_node[Analyser.COMPILATION_COMMAND_KEY],
                r'cl /c /ZI /nologo /W3 /WX- /Od /Oy- /D WIN32 /D _DEBUG /D _CONSOLE /D _UNICODE /D UNICODE /Gm /EHsc /RTC1 /MDd /GS /fp:precise /Zc:wchar_t /Zc:forScope /Zc:inline /Fo"Debug\\" /Fd"Debug\vc140.pdb" /Gd /TP /analyze- /errorReport:prompt /Bt+ /showIncludes /nologo- /FC'
                )
            self.assertAlmostEqual(
                test_cpp_node[Analyser.BUILD_TIME_KEY], 0.04414)

            test_hpp_node = graph.node['test.hpp']
            self.assertNotIn(
                Analyser.COMPILATION_COMMAND_KEY, test_hpp_node)
            self.assertNotIn(
                Analyser.BUILD_TIME_KEY, test_hpp_node)
        finally:
            os.remove(log_path)

    def test_parses_minimal_vs_log(self):
        log_path = tempfile.mktemp()
        try:
            with open(log_path, 'w') as f:
                f.write(self._MINIMAL_LOG)
            depgraph = parse_vs_log(log_path)

            graph = depgraph._graph
            
            nodes = graph.nodes()
            self.assertEqual(sorted(nodes), sorted([
                depgraph._ROOT_NODE_LABEL,
                'test.cpp',
                'stdafx.cpp',
                ]))

            edges = graph.edges()
            self.assertEqual(sorted(edges), sorted([
                (depgraph._ROOT_NODE_LABEL, 'test.cpp'),
                (depgraph._ROOT_NODE_LABEL, 'stdafx.cpp'),
                ]))

            test_cpp_node = graph.node['test.cpp']

            self.assertNotIn(
                Analyser.COMPILATION_COMMAND_KEY, test_cpp_node)
            self.assertNotIn(
                Analyser.BUILD_TIME_KEY, test_cpp_node)
        finally:
            os.remove(log_path)

    def test_handles_duplicated_labels(self):
        log_path = tempfile.mktemp()
        try:
            with open(log_path, 'w') as f:
                f.write(self._DUPLICATED_LABELS_LOG)
            depgraph = parse_vs_log(log_path)

            graph = depgraph._graph
            
            nodes = graph.nodes()
            self.assertEqual(sorted(nodes), sorted([
                depgraph._ROOT_NODE_LABEL,
                'test.cpp',
                'test.cpp_1',
                'test-same.hpp',
                'test-different.hpp',
                'test-different.hpp_1',
                ]))

            edges = graph.edges()
            self.assertEqual(sorted(edges), sorted([
                (depgraph._ROOT_NODE_LABEL, 'test.cpp'),
                (depgraph._ROOT_NODE_LABEL, 'test.cpp_1'),
                ('test.cpp', 'test-same.hpp'),
                ('test.cpp', 'test-different.hpp'),
                ('test.cpp_1', 'test-same.hpp'),
                ('test.cpp_1', 'test-different.hpp_1'),
                ]))

            self.assertAlmostEqual(
                graph.node['test.cpp'][Analyser.ABSOLUTE_PATH_KEY],
                r'd:\work\test\test\test.cpp')
            self.assertAlmostEqual(
                graph.node['test-same.hpp'][Analyser.ABSOLUTE_PATH_KEY],
                r'd:\work\test\test\test-same.hpp')
            self.assertAlmostEqual(
                graph.node['test-different.hpp'][Analyser.ABSOLUTE_PATH_KEY],
                r'd:\work\test\test\test-different.hpp')
            self.assertAlmostEqual(
                graph.node['test.cpp_1'][Analyser.ABSOLUTE_PATH_KEY],
                r'd:\work\test\test-other\test.cpp')
            self.assertAlmostEqual(
                graph.node['test-different.hpp_1'][Analyser.ABSOLUTE_PATH_KEY],
                r'd:\work\test\test-other\test-different.hpp')

        finally:
            os.remove(log_path)

if __name__ == '__main__':
    unittest.main()
