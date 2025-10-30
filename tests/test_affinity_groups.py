from tests import setup_path

setup_path()
import networkx as nx
import plotly.graph_objects as go


def test_edge_width_fix():
    """Test that creating a scatter plot with edge widths works correctly."""
    G = nx.Graph()
    G.add_node("A")
    G.add_node("B")
    G.add_node("C")
    G.add_edge("A", "B", weight=0.5)
    G.add_edge("B", "C", weight=0.8)
    G.add_edge("A", "C", weight=0.3)
    pos = {"A": (0, 0), "B": (1, 1), "C": (2, 0)}
    edge_x = []
    edge_y = []
    edge_weights = []
    for edge in G.edges():
        (x0, y0) = pos[edge[0]]
        (x1, y1) = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_weights.append(G.edges[edge]["weight"])
    max_weight = max(edge_weights) if edge_weights else 1
    edge_traces = []
    for i in range(0, len(edge_x), 3):
        if i + 2 < len(edge_x):
            edge_idx = i // 3
            if edge_idx < len(edge_weights):
                width = 2 + edge_weights[edge_idx] / max_weight * 6
            else:
                width = 2
            edge_trace = go.Scatter(
                x=edge_x[i : i + 3],
                y=edge_y[i : i + 3],
                line=dict(width=width, color="#888"),
                hoverinfo="none",
                mode="lines",
                showlegend=False,
            )
            edge_traces.append(edge_trace)
    node_trace = go.Scatter(
        x=[pos[node][0] for node in G.nodes()],
        y=[pos[node][1] for node in G.nodes()],
        mode="markers",
        marker=dict(size=10, color="blue"),
        text=list(G.nodes()),
        hoverinfo="text",
    )
    fig = go.Figure(data=[*edge_traces, node_trace])


if __name__ == "__main__":
    test_edge_width_fix()
