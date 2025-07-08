from typing import Tuple

import matplotlib.pyplot as plt
import networkx as nx


def visualize_graph(
    G: nx.Graph,
    *,
    metrics: dict | None = None,
    comm_map: dict | None = None,
    layout: str = "spring",
    layout_kwargs: dict = None,
    node_size_by: str = "degree",
    size_scale: float = 100,
    node_color_by: str | None = None,
    cmap: str = "tab10",
    edge_threshold: int | None = None,
    edge_width_scale: float = 0.3,
    show_edge_labels: bool = False,
    node_labels: bool = True,
    figsize: Tuple[int, int] = (8, 6),
    title: str | None = None,
    title_fontsize: float | None = None,
    title_fontweight: str = 'normal',
    title_fontfamily: str = 'sans-serif',
    title_loc: str = 'center',
    title_pad: float | None = None,
    ax: plt.Axes = None
) -> plt.Figure:
    """
    Draws a NetworkX graph with various customization options.

    Parameters:
    - G: The NetworkX graph to visualize.
    - metrics: Optional dict of node metrics (e.g., centrality measures).
    - comm_map: Optional mapping of nodes to community indices.
    - layout: Layout algorithm to use.
    - layout_kwargs: Arguments for the layout function.
    - node_size_by: Metric name to scale node sizes.
    - size_scale: Scaling factor for node sizes.
    - node_color_by: Metric or 'community' to color nodes.
    - cmap: Colormap for categorical coloring.
    - edge_threshold: Minimum weight for edges to display.
    - edge_width_scale: Factor for edge width scaling.
    - show_edge_labels: Whether to label edges with weights.
    - node_labels: Whether to display node names.
    - figsize: Figure size.
    - title: Optional title for the plot.
    - ax: Pre-existing Matplotlib Axes to draw on.

    Returns:
    - Matplotlib Figure object.
    """
    # Prepare layout kwargs, stripping unsupported keys based on algorithm
    layout_kwargs = layout_kwargs.copy() if layout_kwargs else {}
    if layout == "spring":
        # spring_layout accepts e.g. k, seed, weight
        pos = nx.spring_layout(G, **layout_kwargs)
    elif layout == "kamada_kawai":
        # kamada_kawai_layout does not accept 'seed' or 'k'
        layout_kwargs.pop('seed', None)
        layout_kwargs.pop('k', None)
        pos = nx.kamada_kawai_layout(G, **layout_kwargs)
    elif layout == "circular":
        # circular_layout is deterministic; remove seed/k if present
        layout_kwargs.pop('seed', None)
        layout_kwargs.pop('k', None)
        pos = nx.circular_layout(G, **layout_kwargs)
    else:
        # fallback to spring
        pos = nx.spring_layout(G, **layout_kwargs)

    # Prepare figure and axes
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure

    # Filter edges by threshold
    edges = G.edges(data=True)
    if edge_threshold is not None:
        edges = [(u, v, d) for u, v,
                 d in edges if d.get('weight', 1) >= edge_threshold]

    # Draw edges
    for u, v, d in edges:
        weight = d.get('weight', 1)
        ax.plot(
            [pos[u][0], pos[v][0]],
            [pos[u][1], pos[v][1]],
            linewidth=weight * edge_width_scale,
            color='gray'
        )

    # Node sizes
    if node_size_by and metrics:
        sizes = [metrics.get(node, 0) * size_scale for node in G.nodes()]
    else:
        sizes = [size_scale for _ in G.nodes()]

    # Node colors
    if node_color_by == 'community' and comm_map:
        colors = [comm_map.get(node, 0) for node in G.nodes()]
    elif node_color_by and metrics:
        colors = [metrics.get(node, 0) for node in G.nodes()]
    else:
        colors = None

    # Draw nodes
    nx.draw_networkx_nodes(
        G,
        pos,
        node_size=sizes,
        node_color=colors,
        cmap=plt.get_cmap(cmap),
        ax=ax
    )

    # Draw labels
    if node_labels:
        nx.draw_networkx_labels(G, pos, ax=ax)

    # Edge labels
    if show_edge_labels:
        nx.draw_networkx_edge_labels(
            G,
            pos,
            edge_labels={(u, v): f"{d.get('weight', 1):.2f}"
                         for u, v, d in edges},
            ax=ax
        )

    # Set title if provided
    if title:
        title_kwargs = {}
        if title_fontsize is not None:
            title_kwargs['fontsize'] = title_fontsize
        if title_fontweight:
            title_kwargs['fontweight'] = title_fontweight
        if title_fontfamily:
            title_kwargs['fontfamily'] = title_fontfamily
        ax.set_title(title, loc=title_loc, pad=title_pad, **title_kwargs)

    ax.axis('off')
    return fig
