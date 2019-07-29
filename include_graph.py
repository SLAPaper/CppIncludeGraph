"""C++ Include Graph Generator
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


def get_prefix(node: tg.Text) -> tg.Text:
    if node.endswith('.h') or node.endswith('.cpp'):
        return node.rsplit('.', maxsplit=1)[0]
    else:
        return node


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
    CATEGORYLIST = ('cpp', 'h', '"module"', 'other')

    def determ_category(node: tg.Text) -> int:
        """Defer node by there name
        Should be consisdent with CATEGORYLIST
        """
        if node.endswith('cpp'):
            return 0
        if node.endswith('h'):
            return 1
        if node.startswith('[merged]'):
            return 2
        return 3

    def calc_node_size(graph: nx.DiGraph, node: tg.Text) -> int:
        """Size nodes by their degree.
        Use natrual log to make them less diversed
        multiply by SIZE_FACTOR to make them not too small
        plus 1 so that size won't be zero
        """
        SIZE_FACTOR = 3
        return math.floor(SIZE_FACTOR * math.log1p(graph.degree(node))) + 1

    nodes: tg.Sequence[ec.options.GraphNode] = [
        ec.options.GraphNode(name=get_prefix(node),
                             category=determ_category(node),
                             symbol_size=calc_node_size(graph, node))
        for node in graph.nodes()
    ]
    edges: tg.Sequence[ec.options.GraphLink] = [
        ec.options.GraphLink(source=get_prefix(edge[0]),
                             target=get_prefix(edge[1]))
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


def merge_header(graph: nx.DiGraph) -> nx.DiGraph:
    """Merge .h with same name .cpp
    create new [merged] node as fake "module"
    """
    can_merge: tg.MutableMapping[tg.Text, bool] = {}
    for node in graph.nodes():
        prefix = get_prefix(node)
        if prefix in can_merge:
            can_merge[prefix] = True
        else:
            can_merge[prefix] = False

    result = nx.DiGraph()
    for edge in graph.edges():
        prefix0 = get_prefix(edge[0])
        prefix1 = get_prefix(edge[1])
        if can_merge[prefix0] or can_merge[prefix1]:
            new_edge = [edge[0], edge[1]]
            if can_merge[prefix0]:
                new_edge[0] = '[merged]' + prefix0
            if can_merge[prefix1]:
                new_edge[1] = '[merged]' + prefix1
            result.add_edge(*new_edge)
        else:
            result.add_edge(*edge)
    return result


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
    parser.add_argument('--nomerge',
                        action='store_false',
                        help=('disable merging same name .h and .cpp'))

    args = parser.parse_args()

    path: Path = args.path
    include_graph = build_graph(path)
    if args.all:
        if args.nomerge is False:
            draw_graph(include_graph, args.out, args.forcerepulsion)
        else:
            draw_graph(merge_header(include_graph), args.out,
                       args.forcerepulsion)
    else:
        main_subgraph = include_graph.subgraph(
            chain([args.entryfile],
                  nx.descendants(include_graph, args.entryfile)))
        if args.nomerge is False:
            draw_graph(main_subgraph, args.out, args.forcerepulsion)
        else:
            draw_graph(merge_header(main_subgraph), args.out,
                       args.forcerepulsion)
