import networkx as nx
import pytest

from notebook_service.visualization import plot_louvain_communities

pytest.skip("Not ready yet", allow_module_level=True)


def test_visualize_graph_returns_figure():
    # Build a toy graph
    G = nx.path_graph([1, 2, 3])
    # Call your plotting function
    fig = plot_louvain_communities(G)
    # Assert it’s a matplotlib Figure

    assert hasattr(fig, "savefig")
    # Optionally: ensure it has at least one Axes
    assert len(fig.get_axes()) >= 1
