- [Techland C++ Build Profiler](#)
	- [Getting started](#)
	- [Metrics](#)
		- [root metrics](#)
		- [top-level metrics](#)
		- [dependency metrics](#)
	- [Command-line tool](#)
	
Techland C++ Build Profiler
===========================

A tool that attempts to facilitate profiling C++ builds.

For the moment it only supports Visual C++ builds, but other platforms could be easily added.

Getting started
---------------

A typical workflow in a Visual Studio project could look like this.

0. Install cpp-build-profiler using PIP `pip install cppbuildprofiler`
0. Add `/Bt+ /showIncludes /nologo- /FC` to your compiler options in `C/C++ -> Command Line ->
Additional Options`
0. Rebuild the project, copy the build output to a file, put that file in a directory, say `profile/log.txt`.
0. Open up the command prompt and run
`cppbuildprofiler PROFILE_DIR --log-file LOG_FILE_NAME --codebase-dir ABSOLUTE/PATH/TO/SOURCE/DIR`.
You can add the `--column-separator` option, depending on the spreadsheet tool you use. For Google Spreadsheet
use `--column-separator '\t'`. `--codebase-dir` is important to identify third-party dependencies. See
[remove_thirdparty_dependencies](#thirdparty) for more information.
0. Your profile directory will now (hopefully) contain a number of files (for an explanation of metrics see
the "[Metrics](#metrics)" section):
	* *root.csv* - summary of the whole build
	* *top_level.csv* - information of build times of specific c++ files
	* *dependency.csv* - information about `#include`d files
	* *graph.gml* - the project's dependency graph
0. You can now copy the *.csv* file contents into a spreadsheet programme and try to identify the heavy-hitters
in your build. I personally found that the most useful metrics to start with are *aggregated build time deviation
from avg* and *total build time of dependants* in the *dependency* file.
0. After identifying dependencies that have the biggest impact on build times it can be useful to take a look
at the dependency graph using a tool such as [Cytoscape](http://www.cytoscape.org/download.php). If your build
contains a lot of files you can generate a subgraph to see only files related to the inspected file. This can be
done using the `cppbuildprofiler-cli` command-line tool. See the "[Command-line tool](#cli)" section for instructions.
0. Improve and repeat!

<a name="metrics"></a>Metrics
-----------------------------

### *root* metrics

The root node is connected to all top-level nodes and aggregates the information there to provide a summary of
the whole build.

* *total build time [s]* - sum of build times of all top-level files. In parallell builds this value will therefore
be much larger than the actual project building time.
* *total translation units* - speaks for itself
* *total size [B]* - sum of *total size [B]* values of top-level files. This is the total number of bytes of code
compiled.

### *top-level* metrics

* *label* - useful when working with the dependency graph. Use this name to identify nodes. This is normally the
filename, but duplicated files are suffixed with *_NUMBER*
* *project* - name of the project containing the *.cpp* file.
* *absolute path* - make a guess!
* *build time [s]* - total time it took to compile this file
* *file size [B]* - size of the *.cpp* file (without dependencies)
* *total size [B]* - total size of the translation unit. This is the aggregated size of all files in this file's
subtree. Files included through precompiled-headers are excluded from this metric, so this is the actual size
of the compiled code. Headers are assumed to be included only once, so if for some reason you have a file
without an include guard and it should be included twice in the subtree, it will be counted only once.

### *dependency* metrics

* *label* - useful when working with the dependency graph. Use this name to identify nodes. This is normally the
filename, but duplicated files are suffixed with *_NUMBER*
* *project* - name of the project containing the dependency file. This is guessed based on the file's location.
The closest parent directory containing a *.cpp* file is found and this file's project name is assumed to be the
dependency project.
* *absolute path* - well...
* *number of dependent translation units* - number of top-level files including this dependency. Inclusions through
precompiled-headers are not counted.
* *file size [B]* - size of the *.cpp* file (without dependencies)
* *aggregated total size [B]* - the aggregated size of the dependency's subtree, calculated independently for each
translation unit. Files included through precompiled-headers are not counted. For example let's consider the following
structure (indentation means inclusion).
	* *a.cpp*
		* *a.hpp* (10 Bytes)
			* *aa.hpp* (15 Bytes)
			* *b.hpp* (2 Bytes)
				* *bb.hpp* (2 Bytes)
		* *c.hpp*
			* *b.hpp* (2 Bytes)
				* *bb.hpp* (2 Bytes)
	* *b.cpp*
		* *b.hpp* (2 Bytes)
			* *bb.hpp* (2 Bytes)

	*b.hpp* will have an aggregated total size of 6 Bytes - once counted through *a.cpp*, once through *b.cpp*, both times
	counted with *bb.hpp*. *a.hpp* may report to have an aggregated total size of either 29 Bytes or 25 Bytes. This depends
	on the order of graph traversal - either *b.hpp* will be considered as included through *a.hpp* or through *c.hpp*.
* *total build time of dependants [s]* - total time spent on compiling files including this dependency
* *aggregated build time deviation from avg [s]* - this is the sum of signed difference of dependant translation unit's
build time from the average build time. If for example the average build time of a translation unit is 1 second and a
dependency is included in 3 files building 2s, 3s and 0.5s, the value of this metric will be 2.5s. This metric should
essentially tell you the impact a file has on the total build time. A possible way to identify actual culprits of long
build times is to order a spreadsheet by the *aggregated build time deviation from avg* column and look at files with
large *aggregated total size*. Removing dependencies from such files often gives good results.

<a name="cli"></a>Command-line tool
-----------------------------------

<a name="thirdparty"></a>remove_thirdparty_dependencies
