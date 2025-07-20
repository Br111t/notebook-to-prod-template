# tests/notebook_service/test_graph_builder.py
import networkx as nx
import numpy as np
import pandas as pd


def test_preprocess_concepts_exclusion(monkeypatch):
    import notebook_service.graph_builder as gb

    # Override the per‑doc exclusion map so we can test filtering
    monkeypatch.setattr(gb, "EXCLUDE_PER_DOC", {0: {"http://bad"}, 1: set()})
    df = pd.DataFrame({
        "concepts_raw": [
            [
                {"text": "A",
                 "relevance": 0.9,
                 "dbpedia_resource": "http://good"
                 },
                {"text": "B",
                 "relevance": 0.1,
                 "dbpedia_resource": "http://bad"
                 },
            ],
            [
                {"text": "C",
                 "relevance": 0.5,
                 "dbpedia_resource": ""
                 },
            ],
        ]
    })

    out = gb.preprocess_concepts(df)
    # B should be dropped (doc 0), A and C kept
    assert all(out["concept"] != "B")
    assert list(out["doc_index"]) == [0, 1]
    assert list(out["concept"]) == ["A", "C"]


def test_compute_cooccurrence_and_edges():
    import notebook_service.graph_builder as gb
    df = pd.DataFrame({
        "doc_index": [0, 0, 1, 1],
        "concept":   ["X", "Y", "Y", "Z"],
    })
    M, C, edges = gb.compute_cooccurrence(df, threshold=1)

    # Indicator matrix rows and cols
    assert list(M.index) == [0, 1]
    assert set(M.columns) == {"X", "Y", "Z"}

    # Co-occurrence: Y appears twice
    assert C.loc["Y", "Y"] == 2

    # Edges with count >= 1
    assert ("X", "Y", 1) in edges
    assert ("Y", "Z", 1) in edges
    # X–Z never co‑occurred
    assert not any(pair[:2] == ("X", "Z") for pair in edges)


def test_threshold_undirected_graph():
    import notebook_service.graph_builder as gb

    # A small symmetric matrix
    C_arr = np.array([[2, 1, 0],
                      [1, 2, 1],
                      [0, 1, 2]])
    feat_names = ["B", "A", "C"]  # unordered
    G = gb.threshold_undirected_graph(C_arr, feat_names, percentile=50)

    # Should sort feat_names → nodes {'A','B','C'}
    assert set(G.nodes()) == {"A", "B", "C"}

    # Off‑diagonals: [1,1,0] → 50th percentile == 1
    # Keeps edges (A–B) and (B–C)
    edges = {frozenset(e) for e in G.edges()}
    assert {frozenset(("A", "B")), frozenset(("B", "C"))} == edges


def test_detect_and_filter_communities(monkeypatch):
    import notebook_service.graph_builder as gb

    # Build a simple graph
    G = nx.Graph()
    G.add_edge("A", "B", weight=1)
    G.add_edge("B", "C", weight=1)

    # Stub Louvain partition: put A,B in community 0, C in 1
    monkeypatch.setattr(
        gb.community_louvain,
        "best_partition",
        lambda
        graph,
        weight,
        random_state: {"A": 0, "B": 0, "C": 1}
    )

    G_back, keep, partition, sizes = gb.detect_and_filter_communities(
        G,
        min_size=2,
        seed=42)

    # Only community 0 has size ≥2
    assert keep == {0}
    assert set(G_back.nodes()) == {"A", "B"}
    assert partition == {"A": 0, "B": 0}
    assert sizes[0] == 2 and sizes[1] == 1


def test_compute_all_metrics():
    import notebook_service.graph_builder as gb
    G = nx.path_graph(3)  # nodes 0,1,2
    metrics = gb.compute_all_metrics(G)

    # Should include all four centrality measures
    assert set(metrics) == {"pagerank", "betweenness", "eigenvector", "degree"}
    for scores in metrics.values():
        assert set(scores.keys()) == set(G.nodes())


def test_SemanticGraph_end_to_end(monkeypatch):
    import notebook_service.graph_builder as gb

    # Stub community detection so all nodes stay in one community
    monkeypatch.setattr(
        gb.community_louvain,
        "best_partition",
        lambda graph, weight, random_state: {n: 0 for n in graph.nodes()}
    )
    # No exclusions
    monkeypatch.setattr(gb, "EXCLUDE_PER_DOC", {})

    df_concepts = pd.DataFrame({
        "doc_index": [0, 0, 1, 1],
        "concept":   ["M", "N", "N", "O"],
    })
    sg = gb.SemanticGraph(
        df_concepts,
        threshold_count=1,
        percentile=0,      # keep all edges
        min_comm_size=1,   # keep all communities
        seed=42,
    )

    # Check that everything initialized
    assert isinstance(sg.M, pd.DataFrame)
    assert isinstance(sg.C, pd.DataFrame)
    assert isinstance(sg.edges, list)
    assert sg.feat_names == ["M", "N", "O"]
    assert isinstance(sg.G_und, nx.Graph)
    assert set(sg.G.nodes()) == set(sg.feat_names)
    assert set(sg.metrics.keys()) == {
        "pagerank",
        "betweenness",
        "eigenvector",
        "degree"}
