import networkx as nx
import pandas as pd


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    # cleans text, extracts concepts/emotions, etc.
    ...


def build_semantic_graph(df: pd.DataFrame) -> nx.Graph:
    # creates and returns a NetworkX graph
    G = nx.Graph()
    # add nodes/edges based on df
    return G


def compute_centrality(G: nx.Graph) -> dict:
    return nx.degree_centrality(G)
