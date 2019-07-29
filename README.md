# C++ Inlcude Graph Generator

A Python Script that generates all h and cpp file include relationship graph

## Requirements

- Python 3.7+ (lower may work but not tested)
- NetworkX latest version: convinient network manimulation
- PyEcharts latest version: visualization

## Usage

    usage: include_graph.py [-h] [--out OUT] [--entryfile ENTRYFILE] [--all]
                            [--forcerepulsion FORCEREPULSION] [--nomerge]
                            path

    Iterate through a folder and draw include graph

    positional arguments:
    path

    optional arguments:
    -h, --help            show this help message and exit
    --out OUT
    --entryfile ENTRYFILE
                            The file of entrypoint, ignore when using --all.
    --all                 Draw the whole include map, else only decendence of
                            entryfile is included.
    --forcerepulsion FORCEREPULSION
                            Repulsion argument in force layout, which control how
                            far nodes repel each other.
    --nomerge             disable merging same name .h and .cpp

## Example

[gflags/gflags](https://github.com/gflags/gflags) repo(with --all): [Example Page](https://slapaper.github.io/CppIncludeGraph/example(gflags).html)
