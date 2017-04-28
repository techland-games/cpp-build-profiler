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
use `--column-separator '\t'`.
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



<a name="cli"></a>Command-line tool
-----------------------------------


