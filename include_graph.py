"""Include Map
"""

import argparse
import math
import re
import typing as tg
from itertools import chain
from pathlib import Path

import networkx as nx
import pyecharts as ec
import pyecharts.charts as ecc


def build_graph(path: Path) -> nx.DiGraph:
    """Search for cpp and h file,
    find lines include "include" and take the included file to build network
    """
    include_graph = nx.DiGraph()
    for srcfile in chain(path.rglob('*.cpp'), path.rglob('*.h')):
        with srcfile.open('r') as f:
            try:
                for line in f:
                    if re.match(r'#\s*(include|INCLUDE)',
                                line.strip()) is not None:
                        match = re.search('[<"](?P<include>.+)[">]',
                                          line.strip())
                        if match is None:
                            continue
                        included_file = match.group('include')
                        if included_file:
                            include_graph.add_edge(
                                str(srcfile.relative_to(path)),
                                str(included_file))
            except UnicodeDecodeError:
                # some actual file use non-unicode encoding, skip
                pass
    return include_graph


def draw_graph(graph: nx.DiGraph, outpath: Path,
               repulsion: int = 1000) -> None:
    """Use PyEcharts to draw the graph to html
    """
    CATEGORYLIST = ('cpp', 'h', 'other')

    def determ_category(node: tg.Text) -> int:
        """Defer node by there name
        Should be consisdent with CATEGORYLIST
        """
        if node.endswith('cpp'):
            return 0
        if node.endswith('h'):
            return 1
        return 2

    def calc_node_size(graph: nx.DiGraph, node: tg.Text) -> int:
        """Size nodes by their degree.
        Use natrual log to make them less diversed
        multiply by a factor to make them not too small
        """
        return math.floor(3 * math.log1p(graph.degree(node))) + 1

    nodes: tg.Sequence[ec.options.GraphNode] = [
        ec.options.GraphNode(name=node,
                             category=determ_category(node),
                             symbol_size=calc_node_size(graph, node))
        for node in graph.nodes()
    ]
    edges: tg.Sequence[ec.options.GraphLink] = [
        ec.options.GraphLink(source=edge[0], target=edge[1])
        for edge in graph.edges()
    ]
    categories: tg.Sequence[ec.options.GraphCategory] = [
        ec.options.GraphCategory(name=name) for name in CATEGORYLIST
    ]

    chart = (
        ecc.Graph(init_opts=ec.options.InitOpts(  # fill the window
            width="100vw",
            height="100vh",
            page_title="PyEcharts 图表")).add(
                "",
                nodes,
                edges,
                categories,
                repulsion=repulsion,
                edge_symbol=[None, 'arrow']).set_global_opts(
                    tooltip_opts=ec.options.TooltipOpts(is_show=False),
                    title_opts=ec.options.TitleOpts(title='C++依赖关系图')))
    if outpath.is_dir():
        chart.render(outpath / 'render.html')
    else:
        chart.render(outpath)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Iterate through a folder and draw include graph")
    parser.add_argument('path', type=Path)
    parser.add_argument('--out', type=Path, default=Path.cwd())
    parser.add_argument('--entryfile',
                        default='main.cpp',
                        help=('The file of entrypoint, '
                              'ignore when using --all.'))
    parser.add_argument(
        '--all',
        action='store_true',
        help=('Draw the whole include map, '
              'else only decendence of entryfile is included.'))
    parser.add_argument('--forcerepulsion',
                        type=int,
                        default=1000,
                        help=('Repulsion argument in force layout, '
                              'which control how far nodes repel each other.'))
    args = parser.parse_args()

    path: Path = args.path
    include_graph = build_graph(path)
    if args.all:
        draw_graph(include_graph, args.out, args.forcerepulsion)
    else:
        main_subgraph = include_graph.subgraph(
            chain([args.entryfile],
                  nx.descendants(include_graph, args.entryfile)))
        draw_graph(main_subgraph, args.out, args.forcerepulsion)
