from collections import Counter

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from adjustText import adjust_text
from scipy.spatial import ConvexHull


def plot_louvain_communities(
    G: nx.Graph,
    comms: set[int],
    partition: dict[str, int],
    sizes: Counter,
    *,
    pos: dict[str, tuple[float, float]] | None = None,
    layout: str = "spring",
    layout_kwargs: dict = None,
    seed: int,
    min_size: int,
    percentile: float = 99,
    metrics: dict[str, float] | None = None,
    size_by: str | None = None,
    size_scale: float = 200,
    alpha: float = 0.2,
    facecolor: str = "#f9f9f9",
    figsize: tuple[int, int] = (10, 8),
) -> plt.Figure:

    """
    Render a spring-layout Louvain community plot.

    Parameters
    ----------
    G         : nx.Graph, the filtered subgraph of interest
    comms     : set of community IDs kept (>= min_size)
    partition : mapping node -> community ID
    sizes     : Counter of community sizes (for legend)
    seed      : random seed for layout
    min_size  : minimum community size that was kept (for titling)
    percentile: percentile used to threshold edges (for title)
    metrics   : optional mapping node -> metric value for sizing
    size_by   : label of metric used for sizing (for reference)
    size_scale: multiplicative factor for node sizing
    alpha     : change the color of community fill
    background: change the color of graph background
    figsize   : output figure size

    """

    # Prepare layout
    fig, ax = plt.subplots(figsize=figsize)

    # set the overall plot background
    fig.patch.set_facecolor(facecolor)
    ax.set_facecolor(facecolor)

    # Compute positions
    if pos is None:
        layout_kwargs = layout_kwargs or {}
        if layout == "spring":
            pos = nx.spring_layout(G, seed=seed, **layout_kwargs)
        elif layout == "kamada_kawai":
            pos = nx.kamada_kawai_layout(G, **layout_kwargs)
        elif layout == "circular":
            pos = nx.circular_layout(G, **layout_kwargs)
        else:
            raise ValueError(f"Unknown layout: {layout}")

    cmap = plt.get_cmap("tab20")

    # Convex hull per community
    for cid in sorted(comms):
        pts = np.array([pos[n] for n, c in partition.items() if c == cid])
        if pts.shape[0] < 3:
            continue
        hull = ConvexHull(pts)
        poly = plt.Polygon(
            pts[hull.vertices],
            facecolor=cmap(cid),
            alpha=alpha,
            edgecolor=None,
            zorder=1
        )
        ax.add_patch(poly)
        poly.set_transform(ax.transData)

    # Draw edges underneath nodes
    edge_coll = nx.draw_networkx_edges(
       G, pos,
       alpha=0.3,
       edge_color="gray",
       ax=ax
       )
    # bump the edges into the correct stacking order
    edge_coll.set_zorder(2)

    # Compute node sizes & draw nodes
    if size_by and metrics and size_by in metrics:
        vals = metrics[size_by]
        node_sizes = [vals.get(n, 0) * size_scale for n in G.nodes()]
    else:
        node_sizes = [size_scale for _ in G.nodes()]

    # Draw nodes colored by community
    node_coll = nx.draw_networkx_nodes(
        G, pos,
        node_color=[partition[n] for n in G.nodes()],
        cmap=cmap,
        node_size=node_sizes,
        ax=ax
        )
    node_coll.set_zorder(3)

    # after drawing nodes & edges:
    texts = [ax.text(*pos[n], n, fontsize=8) for n in G.nodes()]
    adjust_text(texts, ax=ax,
                expand_text=(1.2, 1.2),
                force_text=0.5)

    # Legend: community IDs and sizes
    patches = [
        mpatches.Patch(color=cmap(cid),
                       label=f"Community {cid} ({sizes[cid]} nodes)")
        for cid in sorted(comms)
    ]
    ax.legend(
        handles=patches,
        title=f"Louvain (min_size={min_size})",
        bbox_to_anchor=(1.02, 1),
        loc="upper left"
    )

    # Title including threshold info
    ax.set_title(
        f"Louvain Communities (≥{min_size} nodes, " +
        "top {100-percentile:.1f}% edges)",
        fontsize=16
    )
    ax.axis('off')
    plt.tight_layout()

    return fig
