from collections import Counter

import networkx as nx
import pytest

from notebook_service.visualization import plot_louvain_communities


def make_simple_graph():
    G = nx.Graph()
    # Create a triangle so ConvexHull code runs
    G.add_edge('A', 'B', weight=1)
    G.add_edge('B', 'C', weight=1)
    G.add_edge('A', 'C', weight=1)
    return G


def test_plot_basic_spring():
    G = make_simple_graph()
    comms = {0}
    partition = {n: 0 for n in G.nodes()}
    sizes = Counter({0: len(G)})

    # provide explicit triangular positions so ConvexHull will always run
    pos = {'A': (0, 0), 'B': (1, 0), 'C': (0, 1)}

    fig = plot_louvain_communities(
        G,
        comms,
        partition,
        sizes,
        pos=pos,
        seed=42,
        min_size=1
    )
    assert hasattr(fig, 'savefig')
    axes = fig.get_axes()[0]
    assert len(fig.get_axes()) >= 1
    # with the provided pos, the convex hull patch should be drawn
    assert len(axes.patches) >= 1


def test_plot_with_custom_pos_and_metrics():
    G = make_simple_graph()
    comms = {0}
    partition = {n: 0 for n in G.nodes()}
    sizes = Counter({0: len(G)})
    # custom positions that form a triangle
    pos = {'A': (0, 0), 'B': (1, 0), 'C': (0, 1)}
    metrics = {'pagerank': {'A': 1.0, 'B': 2.0, 'C': 3.0}}

    fig = plot_louvain_communities(
        G,
        comms,
        partition,
        sizes,
        pos=pos,
        layout='spring',  # ignored since pos is given
        layout_kwargs={'k': 0.1},
        seed=0,
        min_size=1,
        metrics=metrics,
        size_by='pagerank',
        size_scale=50
    )
    # Verify nodes are sized by metrics (some text labels exist)
    texts = fig.get_axes()[0].texts
    labels = [t.get_text() for t in texts]
    assert set(labels) == set(G.nodes())


def test_plot_other_layouts():
    G = make_simple_graph()
    comms = {0}
    partition = {n: 0 for n in G.nodes()}
    sizes = Counter({0: len(G)})

    for layout in ('kamada_kawai', 'circular'):
        fig = plot_louvain_communities(
            G,
            comms,
            partition,
            sizes,
            seed=1,
            min_size=1,
            layout=layout
        )
        assert len(fig.get_axes()) >= 1


def test_plot_invalid_layout():
    G = make_simple_graph()
    comms = {0}
    partition = {n: 0 for n in G.nodes()}
    sizes = Counter({0: len(G)})

    with pytest.raises(ValueError):
        plot_louvain_communities(
            G,
            comms,
            partition,
            sizes,
            seed=1,
            min_size=1,
            layout='unknown_layout'
        )
