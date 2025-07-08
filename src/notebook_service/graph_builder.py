# graph_builder.py
import json
from itertools import combinations
from pathlib import Path

import networkx as nx
import pandas as pd
from networkx import DiGraph, Graph
from networkx.algorithms.community import greedy_modularity_communities
from sklearn.preprocessing import MultiLabelBinarizer

# Load per-document exclusions from JSON config
CONFIG_DIR = Path(__file__).parent / "config"
config_path = CONFIG_DIR / "dbpedia_exclusions.json"
if not config_path.exists():
    raise FileNotFoundError(f"Exclusions config not found: {config_path}")
with open(config_path, "r", encoding="utf-8") as f:
    # JSON keys are strings; convert to int and to set
    raw = json.load(f)
    EXCLUDE_PER_DOC = {int(doc): set(urls) for doc, urls in raw.items()}


def preprocess_concepts(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Clean and filter NLU-extracted concepts.

    - Drops concepts with relevance < threshold.
    - Drops any concepts matching JUNK_RE.
    - Optionally run spaCy NER to drop PERSON/WORK_OF_ART
        (uncomment if needed).
    - Excludes DBpedia resources per-document as defined
        in dbpedia_exclusions.json.

    Returns a DataFrame with columns:
      ['doc_index', 'concept', 'relevance', 'concepts_filtered']
    Only includes docs that have ≥1 kept concept,
        and preserves original df order.
    """

    records = []
    for idx, row in df.iterrows():
        to_exclude = EXCLUDE_PER_DOC.get(idx, set())
        for c in row.get("concepts_raw", []):
            text = c.get("text", "")
            rel = c.get("relevance", 0)
            dbp = c.get("dbpedia_resource", "")

            # per-doc resource exclusion
            if dbp in to_exclude:
                continue

            records.append({"doc_index": idx, "concept": text,
                            "relevance": rel})

    dfc = pd.DataFrame(records)
    df_clean = (
        dfc
        .sort_values(["doc_index", "relevance"], ascending=[True, False])
        .reset_index(drop=True)
    )

    return df_clean


def compute_cooccurrence(
    df_concepts: pd.DataFrame,
    threshold: int = 1
) -> tuple[pd.DataFrame, pd.DataFrame, list[tuple[str, str, int]]]:
    """
    Given a DataFrame with columns ['doc_index', 'concept'],
    - Groups concepts by document index
    - Builds the document×concept indicator matrix M
    - Computes co-occurrence matrix C = M.T @ M
    - Filters edges with weight >= threshold

    Returns:
      M (DataFrame): indicator matrix, rows=doc_index, cols=concepts
      C (DataFrame): co-occurrence counts, rows=cols=concepts
      edges (list): list of (concept_a, concept_b, weight)
    """
    # Aggregate per-document concept lists
    doc2concepts = (
        df_concepts
        .groupby('doc_index')['concept']
        .apply(list)
        .sort_index()
    )

    # Binary indicator matrix
    mlb = MultiLabelBinarizer()
    M = pd.DataFrame(
        mlb.fit_transform(doc2concepts),
        index=doc2concepts.index,
        columns=mlb.classes_,
    )

    # Co-occurrence
    C = M.T.dot(M)

    # Threshold edges
    edges = [
        (a, b, int(C.loc[a, b]))
        for a, b in combinations(mlb.classes_, 2)
        if C.loc[a, b] >= threshold
    ]

    return M, C, edges


def build_semantic_graph(
    df_concepts: pd.DataFrame,
    threshold: int = 1,
    directed: bool = False
) -> nx.Graph | nx.DiGraph:
    """
    Build either an undirected or directed co-occurrence graph.
    - undirected: symmetric co-occurrence edges
    - directed: edge A->B only if A precedes B in the doc’s concept list
    """
    M, C, edges = compute_cooccurrence(df_concepts, threshold)

    G = DiGraph() if directed else Graph()
    G.add_nodes_from(C.index)

    if not directed:
        # as before
        G.add_weighted_edges_from(edges)
    else:
        # for each document, add directed edges in the order they appeared
        # assuming df_concepts is ordered by doc_index and then by original
        # sequence
        for doc, grp in df_concepts.groupby("doc_index"):
            seq = grp["concept"].tolist()
            for a, b in zip(seq, seq[1:]):
                if G.has_edge(a, b):
                    G[a][b]["weight"] += 1
                else:
                    G.add_edge(a, b, weight=1)
    return G


def compute_centrality(G: nx.Graph) -> dict:
    """
    Compute and return degree centrality mapping for G.
    """
    return nx.degree_centrality(G)


def detect_communities(G):
    """
    Partition G into communities by greedy modularity maximization.
    Returns a list of frozensets (each set is one community).
    """
    return list(greedy_modularity_communities(G, weight="weight"))


def node_to_community_map(communities):
    return {node: ci for ci, comm in enumerate(communities) for node in comm}


class SemanticGraph:
    def __init__(self, df_concepts, threshold=1):
        self.M, self.C, self.edges = compute_cooccurrence(df_concepts,
                                                          threshold)
        self.G = build_semantic_graph(df_concepts, threshold)
        self.metrics = compute_centrality(self.G)
        self.communities = detect_communities(self.G)
        self.comm_map = node_to_community_map(self.communities)
