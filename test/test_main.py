# Copyright (c) Techland. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.

import unittest
import tempfile
import os
import networkx as nx
from cppbuildprofiler import __main__, DependencyGraph

class TestMain(unittest.TestCase):

    _BUILD_LOG = r'''
1>------ Rebuild All started: Project: test, Configuration: Debug x64 ------
2>------ Rebuild All started: Project: test-lib, Configuration: Debug x64 ------
1>  Microsoft (R) C/C++ Optimizing Compiler Version 19.00.24215.1 for x64
1>  Copyright (C) Microsoft Corporation.  All rights reserved.
1>
1>  cl /c /ZI /nologo /W3 /WX- /Od /D _DEBUG /D _CONSOLE /D _UNICODE /D UNICODE /Gm /EHsc /RTC1 /MDd /GS /fp:precise /Zc:wchar_t /Zc:forScope /Zc:inline /Fo"x64\Debug\\" /Fd"x64\Debug\vc140.pdb" /Gd /TP /errorReport:prompt /Bt+ /showIncludes /nologo- /FC test.cpp
2>  Microsoft (R) C/C++ Optimizing Compiler Version 19.00.24215.1 for x64
1>cl : Command line warning D9035: option 'nologo-' has been deprecated and will be removed in a future release
2>  Copyright (C) Microsoft Corporation.  All rights reserved.
1>cl : Command line warning D9025: overriding '/nologo' with '/nologo-'
2>
1>
2>  cl /c /ZI /nologo /W3 /WX- /sdl /Od /D _DEBUG /D _LIB /D _UNICODE /D UNICODE /Gm /EHsc /RTC1 /MDd /GS /fp:precise /Zc:wchar_t /Zc:forScope /Zc:inline /Yc"stdafx.h" /Fp"x64\Debug\test-lib.pch" /Fo"x64\Debug\\" /Fd"x64\Debug\test-lib.pdb" /Gd /TP /errorReport:prompt /Bt+ /showIncludes /nologo- /FC stdafx.cpp
2>cl : Command line warning D9035: option 'nologo-' has been deprecated and will be removed in a future release
2>cl : Command line warning D9025: overriding '/nologo' with '/nologo-'
2>
2>  stdafx.cpp
1>  test.cpp
2>  Note: including file: d:\work\test\test-lib\stdafx.h
2>  Note: including file:  d:\work\test\test-lib\test-lib.hpp
2>  Note: including file:  d:\work\test\test-lib\test-lib2.hpp
2>  Note: including file:   C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\memory
1>  Note: including file: d:\work\test\test\test.hpp
1>  Note: including file: d:\work\test\test\test2.hpp
2>  Note: including file:    C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\xmemory
1>  Note: including file: d:\work\test\test\../test-lib/test-lib.hpp
2>  Note: including file:     C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\xmemory0
1>  Note: including file: C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\vector
2>  Note: including file:      C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\cstdint
1>  Note: including file:  C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\xmemory
2>  Note: including file:       C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\yvals.h
1>  Note: including file:   C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\xmemory0
2>  Note: including file:        C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\xkeycheck.h
1>  Note: including file:    C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\cstdint
2>  Note: including file:        C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\crtdefs.h
1>  Note: including file:     C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\yvals.h
2>  Note: including file:         C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\vcruntime.h
2>  Note: including file:          C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\sal.h
1>  Note: including file:      C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\xkeycheck.h
2>  Note: including file:           C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\ConcurrencySal.h
1>  Note: including file:      C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\crtdefs.h
2>  Note: including file:          C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\vadefs.h
1>  Note: including file:       C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\vcruntime.h
1>  Note: including file:        C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\sal.h
1>  Note: including file:         C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\ConcurrencySal.h
1>  Note: including file:        C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\vadefs.h
2>  Note: including file:         C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt.h
2>  Note: including file:          C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\vcruntime.h
2>  Note: including file:        C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\use_ansi.h
1>  Note: including file:       C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt.h
2>  Note: including file:       C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\stdint.h
1>  Note: including file:        C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\vcruntime.h
2>  Note: including file:        C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\vcruntime.h
1>  Note: including file:      C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\use_ansi.h
2>  Note: including file:      C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\cstdlib
1>  Note: including file:     C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\stdint.h
2>  Note: including file:       C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\stdlib.h
1>  Note: including file:      C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\vcruntime.h
2>  Note: including file:        C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt_malloc.h
1>  Note: including file:    C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\cstdlib
2>  Note: including file:        C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt_search.h
1>  Note: including file:     C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\stdlib.h
2>  Note: including file:         C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\stddef.h
1>  Note: including file:      C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt_malloc.h
2>  Note: including file:        C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt_wstdlib.h
1>  Note: including file:      C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt_search.h
1>  Note: including file:       C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\stddef.h
1>  Note: including file:      C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt_wstdlib.h
2>  Note: including file:        C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\limits.h
2>  Note: including file:         C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\vcruntime.h
1>  Note: including file:      C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\limits.h
1>  Note: including file:       C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\vcruntime.h
2>  Note: including file:      C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\limits
2>  Note: including file:       C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\ymath.h
2>  Note: including file:       C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\cfloat
2>  Note: including file:        C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\float.h
1>  Note: including file:    C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\limits
1>  Note: including file:     C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\ymath.h
2>  Note: including file:       C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\climits
1>  Note: including file:     C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\cfloat
2>  Note: including file:       C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\cmath
1>  Note: including file:      C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\float.h
2>  Note: including file:        C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\math.h
1>  Note: including file:     C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\climits
1>  Note: including file:     C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\cmath
1>  Note: including file:      C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\math.h
2>  Note: including file:        C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\xtgmath.h
1>  Note: including file:      C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\xtgmath.h
1>  Note: including file:       C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\xtr1common
2>  Note: including file:         C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\xtr1common
1>  Note: including file:     C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\cwchar
2>  Note: including file:       C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\cwchar
1>  Note: including file:      C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\wchar.h
2>  Note: including file:        C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\wchar.h
1>  Note: including file:       C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt_memcpy_s.h
2>  Note: including file:         C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt_memcpy_s.h
1>  Note: including file:        C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\errno.h
2>  Note: including file:          C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\errno.h
1>  Note: including file:        C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\vcruntime_string.h
2>  Note: including file:          C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\vcruntime_string.h
1>  Note: including file:         C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\vcruntime.h
2>  Note: including file:           C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\vcruntime.h
1>  Note: including file:       C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt_wconio.h
2>  Note: including file:         C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt_wconio.h
1>  Note: including file:        C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt_stdio_config.h
2>  Note: including file:          C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt_stdio_config.h
1>  Note: including file:       C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt_wctype.h
2>  Note: including file:         C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt_wctype.h
1>  Note: including file:       C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt_wdirect.h
2>  Note: including file:         C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt_wdirect.h
1>  Note: including file:       C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt_wio.h
2>  Note: including file:         C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt_wio.h
1>  Note: including file:        C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt_share.h
2>  Note: including file:          C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt_share.h
1>  Note: including file:       C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt_wprocess.h
2>  Note: including file:         C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt_wprocess.h
1>  Note: including file:       C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt_wstdio.h
2>  Note: including file:         C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt_wstdio.h
1>  Note: including file:       C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt_wstring.h
2>  Note: including file:         C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt_wstring.h
1>  Note: including file:       C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt_wtime.h
2>  Note: including file:         C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt_wtime.h
1>  Note: including file:       C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\sys/stat.h
2>  Note: including file:         C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\sys/stat.h
1>  Note: including file:        C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\sys/types.h
2>  Note: including file:          C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\sys/types.h
1>  Note: including file:     C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\xstddef
2>  Note: including file:       C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\xstddef
1>  Note: including file:      C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\cstddef
2>  Note: including file:        C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\cstddef
1>  Note: including file:      C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\initializer_list
2>  Note: including file:        C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\initializer_list
1>  Note: including file:    C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\new
2>  Note: including file:      C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\new
1>  Note: including file:     C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\exception
2>  Note: including file:       C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\exception
1>  Note: including file:      C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\type_traits
2>  Note: including file:        C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\type_traits
1>  Note: including file:      C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\malloc.h
2>  Note: including file:        C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\malloc.h
1>  Note: including file:      C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\vcruntime_exception.h
1>  Note: including file:       C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\eh.h
1>  Note: including file:        C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt_terminate.h
2>  Note: including file:        C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\vcruntime_exception.h
1>  Note: including file:     C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\vcruntime_new.h
2>  Note: including file:         C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\eh.h
1>  Note: including file:      C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\vcruntime.h
2>  Note: including file:          C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt_terminate.h
1>  Note: including file:    C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\xutility
2>  Note: including file:       C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\vcruntime_new.h
1>  Note: including file:     C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\utility
2>  Note: including file:        C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\vcruntime.h
1>  Note: including file:      C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\iosfwd
2>  Note: including file:      C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\xutility
1>  Note: including file:       C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\cstdio
2>  Note: including file:       C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\utility
1>  Note: including file:        C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\stdio.h
2>  Note: including file:        C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\iosfwd
1>  Note: including file:       C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\cstring
2>  Note: including file:         C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\cstdio
1>  Note: including file:        C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\string.h
2>  Note: including file:          C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\stdio.h
1>  Note: including file:         C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt_memory.h
2>  Note: including file:         C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\cstring
1>  Note: including file:       C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\crtdbg.h
2>  Note: including file:          C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\string.h
1>  Note: including file:        C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\vcruntime_new_debug.h
2>  Note: including file:           C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\corecrt_memory.h
1>  Note: including file:    C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\xatomic0.h
2>  Note: including file:         C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt\crtdbg.h
1>  Note: including file:    C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\intrin.h
2>  Note: including file:          C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\vcruntime_new_debug.h
1>  Note: including file:     C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\vcruntime.h
2>  Note: including file:      C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\xatomic0.h
1>  Note: including file:     C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\setjmp.h
2>  Note: including file:      C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\intrin.h
1>  Note: including file:      C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\vcruntime.h
2>  Note: including file:       C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\vcruntime.h
1>  Note: including file:     C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\immintrin.h
2>  Note: including file:       C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\setjmp.h
1>  Note: including file:      C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\wmmintrin.h
2>  Note: including file:        C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\vcruntime.h
1>  Note: including file:       C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\nmmintrin.h
2>  Note: including file:       C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\immintrin.h
1>  Note: including file:        C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\smmintrin.h
2>  Note: including file:        C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\wmmintrin.h
1>  Note: including file:         C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\tmmintrin.h
2>  Note: including file:         C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\nmmintrin.h
1>  Note: including file:          C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\pmmintrin.h
2>  Note: including file:          C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\smmintrin.h
1>  Note: including file:           C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\emmintrin.h
2>  Note: including file:           C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\tmmintrin.h
1>  Note: including file:            C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\xmmintrin.h
2>  Note: including file:            C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\pmmintrin.h
1>  Note: including file:             C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\mmintrin.h
2>  Note: including file:             C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\emmintrin.h
1>  Note: including file:     C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\ammintrin.h
2>  Note: including file:              C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\xmmintrin.h
1>  Note: including file:  C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\stdexcept
2>  Note: including file:               C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\mmintrin.h
1>  Note: including file:   C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\xstring
1>  time(C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\bin\amd64\c1xx.dll)=0.17279s < 74955554364 - 74956129414 > BB [D:\work\test\test\test.cpp]
2>  Note: including file:       C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\ammintrin.h
2>  Note: including file:    C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\typeinfo
1>  time(C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\bin\amd64\c2.dll)=0.00682s < 74956134840 - 74956157554 > BB [D:\work\test\test\test.cpp]
2>  Note: including file:     C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\vcruntime_typeinfo.h
2>  Note: including file:      C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\include\vcruntime.h
2>  time(C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\bin\amd64\c1xx.dll)=0.17139s < 74955550379 - 74956120798 > BB [D:\work\test\test-lib\stdafx.cpp]
2>  time(C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\bin\amd64\c2.dll)=0.00688s < 74956127713 - 74956150618 > BB [D:\work\test\test-lib\stdafx.cpp]
2>  test-lib.vcxproj -> D:\work\test\x64\Debug\test-lib.lib
1>  test.vcxproj -> D:\work\test\x64\Debug\test.exe
1>  test.vcxproj -> D:\work\test\x64\Debug\test.pdb (Full PDB)
========== Rebuild All: 2 succeeded, 0 failed, 0 skipped ==========
    '''

    def test_cmd_pipeline(self):
        log_file = tempfile.mktemp(prefix='build-log')
        pre_graph_file = tempfile.mktemp(prefix='pre-graph')
        graph_file = tempfile.mktemp(prefix='graph')
        try:
            with open(log_file, 'w') as output_file:
                output_file.write(self._BUILD_LOG)

            interpreter = __main__.Interpreter()
            interpreter.onecmd('parse_vs_log %s' % log_file)
            interpreter.onecmd(r'store %s' % pre_graph_file)

            result = DependencyGraph.read(pre_graph_file)
            self.assertTrue(result.has_node('test.cpp'))
            self.assertTrue(result.has_node('test.hpp'))
            self.assertTrue(result.has_node('test2.hpp'))
            self.assertTrue(result.has_node('test-lib.hpp'))
            self.assertTrue(result.has_node('vector'))
            self.assertTrue(result.has_node('xmemory'))
            self.assertTrue(result.has_node('stdafx.cpp'))
            self.assertTrue(result.has_node('stdafx.h'))
            self.assertTrue(result.has_node('test-lib2.hpp'))
            self.assertTrue(result.has_node('memory'))

            interpreter_load_store = __main__.Interpreter()
            interpreter_load_store.onecmd(r'load %s' % pre_graph_file)
            interpreter_load_store.onecmd(r'remove_nodes --absolute-path stdafx')
            interpreter_load_store.onecmd(r'remove_thirdparty_dependencies D:/work/test')
            interpreter_load_store.onecmd(r'store %s' % graph_file)

            result = DependencyGraph.read(graph_file)
            self.assertTrue(result.has_node('test.cpp'))
            self.assertTrue(result.has_node('test.hpp'))
            self.assertTrue(result.has_node('test2.hpp'))
            self.assertTrue(result.has_node('test-lib.hpp'))
            self.assertTrue(result.has_node('vector'))
            self.assertFalse(result.has_node('xmemory'))
            self.assertFalse(result.has_node('stdafx.cpp'))
            self.assertFalse(result.has_node('stdafx.h'))
            self.assertFalse(result.has_node('test-lib2.hpp'))
            self.assertFalse(result.has_node('memory'))
        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)
            if os.path.exists(pre_graph_file):
                os.unlink(pre_graph_file)
            if os.path.exists(graph_file):
                os.unlink(graph_file)

if __name__ == '__main__':
    unittest.main()
