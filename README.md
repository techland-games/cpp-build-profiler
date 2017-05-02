**Table of Contents**  *generated with [DocToc](http://doctoc.herokuapp.com/)*
- [Techland C++ Build Profiler](#top)
	- [Getting started](#gettingstarted)
	- [Metrics](#metrics)
		- [root metrics](#root)
		- [top-level metrics](#toplevel)
		- [dependency metrics](#dependency)
	- [The cppbuildprofiler script](#script)
	- [Command-line tool](#cli)
	- [Third-party dependencies](#thirdparty)
	
<a name="top"></a>Techland C++ Build Profiler
=============================================

A tool that attempts to facilitate profiling C++ builds.

For the moment it only supports Visual C++ builds, but other platforms could be easily added.

<a name="gettingstarted"></a>Getting started
--------------------------------------------

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

### <a name="root"></a>*root* metrics

The root node is connected to all top-level nodes and aggregates the information there to provide a summary of
the whole build.

* *total build time [s]* - sum of build times of all top-level files. In parallell builds this value will therefore
be much larger than the actual project building time.
* *total translation units* - speaks for itself
* *total size [B]* - sum of *total size [B]* values of top-level files. This is the total number of bytes of code
compiled.

### <a name="toplevel"></a>*top-level* metrics

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

### <a name="dependency"></a>*dependency* metrics

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

<a name="script"></a>The cppbuildprofiler script
------------------------------------------------

The `cppbuildprofiler` script loads a compilation log, builds a dependency graph, analyses it and outputs a number of files:
* *root.csv* - summary of the whole build
* *top_level.csv* - information of build times of specific c++ files
* *dependency.csv* - information about `#include`d files
* *graph.gml* - the project's dependency graph

The switches available may be printed out by running `cppbuildprofiler --help`. For information on the meaning of the
CODEBASE-DIR in `--codebase-dir` see the [thirdparty dependencies](#thirdparty) section.

<a name="cli"></a>Command-line tool
-----------------------------------

The command-line tool, executed by running `cppbuildprofiler-cli` may be used to perform more tailor-made analyses than
these done by default using `cppbuildprofiler`. Bear in mind that when working with the tool all commands apply changes
to the current dependency graph in memory. If you generate a subgraph containing only the dependencies of some file, all
its predecessors will be removed and to access them again you'll have to re-load the graph.

Available commands are:

* `help` - displays a list of available commands.
* `help COMMAND` or `COMMAND -h` - displays help on the usage of COMMAND.
* `parse_vs_log LOG_FILE` - parses a VisualC++ build log and creates a bare dependency graph.
* `analyse` - runs a full analysis of the dependency graph (calculates all the metrics).
* `remove_thirdparty_dependencies CODEBASE_ROOT` - removes [thirdparty dependencies](#thirdparty) from the graph. Note that this won't update the metrics.
* `store GML_FILE` - stores the current dependency graph to a .gml file.
* `load GML_FILE` - replaces the dependency graph in memory with the one loaded from the .gml file.
* `get_project_dependency_graph FILE` - creates a dependency graph of projects and stores it in the .gml file specified. Note that this will not modify the dependency graph in any way.
* `subgraph -o LABEL [--dependants] [--dependencies]` - the dependency graph in memory is replaced by its subgraph. The subgraph contains the node denoted by LABEL and
	* if `--dependants` is specified: all the nodes that depend on that node
	* if `--dependencies` is specified: all the nodes that the node depends on
* `print` - prints the dependency graph nodes in csv format. Run with `-h` to see the available options.
* `set_verbosity DEBUG|INFO` - changes the amount of logs the programme prints.
* `shell COMMAND` - will execute COMMAND in the underlying shell.

<a name="thirdparty"></a>Third-party dependencies
-------------------------------------------------

Usually, we are not interested in dependencies introduced by headers included from third-party code.
E.g. if we `#include <vector>` this dependency suffices in the graph, we don't need to see that it also includes
`xmemory`, `yvals.h` and whatnot. `cppbuildprofiler` removes these automatically if provided with the `--codebase-dir`
switch and `cppbuildprofiler-cli` removes them with the `remove_thirdparty_dependencies` command. Removing third-party
dependencies should be done *after* running `analyse` as otherwise the *total size* and *aggregated total size* metrics
will be incorrect.

A dependency is considered to be third-party if it lays outside the provided *CODEBASE-DIR*. Let's consider the following
scenario:

0. our code lays in 'd:/code/profiled-project',
0. it includes 'utility-lib.h' from 'd:/code/utility-lib',
0. 'utility-lib.h' includes 'detail.h' from the same directory. This file is *NOT* `#include`d by any of our source files,
0. 'utility-lib.h' also includes 'utility-lib-fwd.h' which *IS* `#include`d by our source files,
0. we run `cppbuildprofiler ... --codebase-dir d:/code/profiled-project`.

The resulting analysis will contain information about *utility-lib.h* and *utility-lib-fwd.h* as they are both immediate
dependencies of our code, but it won't contain *detail.h* as it is a purely third-party dependency.
