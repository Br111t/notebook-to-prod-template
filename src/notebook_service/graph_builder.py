# graph_builder.py
import json
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Dict

import community as community_louvain
import networkx as nx
import numpy as np
import pandas as pd
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


def threshold_undirected_graph(
    C: pd.DataFrame | np.ndarray,
    feat_names: list[str],
    percentile: float,
) -> nx.Graph:
    """
    Prune G_und by keeping edges in the top percentile (of C weights).
    """
    # -- Data prep (assumes df_concepts and C exist) --
    feat_names = sorted(feat_names)
    C_arr = np.asarray(C)
    assert C_arr.shape == (len(feat_names), len(feat_names))

    # 1) threshold edges
    i, j = np.triu_indices_from(C_arr, k=1)
    thresh = np.percentile(C_arr[i, j], percentile)
    C_thresh = np.zeros_like(C_arr)
    C_thresh[C_arr >= thresh] = C_arr[C_arr >= thresh]

    np.fill_diagonal(C_thresh, 0)

    # 2) build graph, relabel
    G = nx.from_numpy_array(C_thresh)
    G = nx.relabel_nodes(G, {i: feat for i, feat in enumerate(feat_names)})

    return G


def detect_and_filter_communities(
    G: nx.Graph,
    min_size: int,
    seed: int,
) -> tuple[nx.Graph, set[int], dict[str, int], Counter]:
    """
    Run Louvain and drop communities smaller than min_size.
    """
    # louvain partition
    l_partition = community_louvain.best_partition(
        G,
        weight="weight",
        random_state=seed
    )

    # filter small communities
    sizes = Counter(l_partition.values())
    keep = {cid for cid, sz in sizes.items() if sz >= min_size}
    # fallback keep largest if none
    if not keep:
        keep = {sizes.most_common(1)[0][0]}
    nodes = [n for n, cid in l_partition.items() if cid in keep]
    G_back = G.subgraph(nodes).copy()
    partition = {n: l_partition[n] for n in nodes}

    return G_back, keep, partition, sizes


def compute_all_metrics(
        G: nx.Graph,
        weight: str = "weight"
) -> Dict[str, Dict[str, float]]:
    """
    Compute a suite of centrality scores on G.

    Returns a dict of metric_name -> { node: score, ... }.
    """
    pr = nx.pagerank(G, weight=weight)
    bc = nx.betweenness_centrality(G, weight=weight)
    ev = nx.eigenvector_centrality(G, weight=weight)
    dc = nx.degree_centrality(G)

    return {
        "pagerank": pr,
        "betweenness": bc,
        "eigenvector": ev,
        "degree": dc,
    }


class SemanticGraph:
    def __init__(
        self,
        df_concepts: pd.DataFrame,
        threshold_count: int = 1,
        percentile: float = 99,
        min_comm_size: int = 9,
        seed: int = 42,
    ):
        # Raw co-occurrence matrix
        self.M, self.C, self.edges = compute_cooccurrence(
            df_concepts,
            threshold_count
        )
        self.feat_names = sorted(df_concepts['concept'].unique())

        # Build undirected backbone by percentile only
        self.G_und = threshold_undirected_graph(
            self.C,
            self.feat_names,
            percentile=percentile,
        )

        # Detect and filter communities
        (
            self.G,
            self.keep,
            self.partition,
            self.sizes
        ) = detect_and_filter_communities(self.G_und, min_comm_size, seed)

        # Compute centrality metrics on the filtered graph
        self.metrics = compute_all_metrics(self.G)

        # Store parameters
        self.percentile = percentile
        self.min_comm_size = min_comm_size
        self.seed = seed
