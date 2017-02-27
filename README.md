Techland C++ Build Profiler
===========================

A tool that attempts to facilitate profiling C++ builds.

Getting started
---------------

You can launch the command line interface by running `cpp-build-profiler`. You can see
a list of available commands by running `help` or `help _command_` for help on a specific
command.

A typical workflow in a Visual Studio project could look like this.

0. Add `/Bt+ /showIncludes /nologo- /FC` to your compiler options in `C/C++ -> Command Line ->
Additional Options`
0. Rebuild the project, copy the build output to a file
0. Open up the command prompt and run `cpp-build-profiler`
0. Run `parse_vs_log <i>path/to/the/log/file</i>`
0. Clean-up some unnecessary files by running `remove_pch` and
`remove_thirdparty_dependencies PATH_TO_CODEBASE_ROOT` - the first command will remove files
that were only included by precompiled headers, the other will remove files included by files 
from outside of your codebase (e.g. this will not remove <vector>, but will remove <xmemory>)
0. Run `analyse` - this will run statistics on the remaining files
0. Run `store PATH_TO_GRAPH.gml` - this will store the dependency graph in a .gml file. You can
then load this graph by calling `load PATH_TO_GRAPH.gml` or import it into a graph visualisation
tool, such as [Cytoscape](http://www.cytoscape.org/download.php)
0. You can then print the statistics for all files in the dependency graph by executing
`print -M -o PATH_TO_OUTPUT.csv` and import the data into a spreadsheet. I recommend promptly adding
an `approximate time spent [s]` column into such spreadsheet, which will multiply values from the
`total subtree size [B]` and `total translation unit build time to size ratio [s/B]` columns. I find it
to be a good indicator of the impact a header file has on the overall build time.
0. If you wish to generate a subgraph of the current dependency graph you can use the `subgraph`
command. For instance, if you wish to get all dependencies of _graphics.h_ run
`subgraph graphics.h --dependencies`. Similarly you could employ `--dependants` or both to generate
a subgraph of all files dependent and being-depended-upon. Bear in mind that the subgraph becoms
the now active graph and as such needs to be `store`d for later access. If you want to access the
full graph you'll need to `load` it.
